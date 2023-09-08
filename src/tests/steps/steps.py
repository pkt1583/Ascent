import datetime
import json
import logging
import os
from uuid import uuid4

from behave import *
from deepdiff import DeepDiff
from jose import jwt

import tests.common.common
from app.core.auth.exception import UnAuthorizedException
from app.core.config import get_settings
from app.core.models import models
from app.core.models.applications import Application
from app.core.models.clusters import Cluster
from app.core.models.deployment import Deployment
from app.core.schemas.applications import ApplicationResponse
from app.core.schemas.clusters import ClusterResponse
from app.core.schemas.deployment import DeploymentState
from app.core.schemas.namespaces import NamespaceListResponse
from app.core.services.applications import get_apps_by_selector
from app.core.services.clusters import get_clusters_by_selector
from app.utils.constants import APP_SERVICE_ID_TOKEN_HEADER, APP_SERVICE_ACCESS_TOKEN_HEADER
from tests.common.common import common_headers, ready_db_object_for_query
from tests.steps import utils
from tests.steps.utils import get_url_and_file_path, converted_file_path, convert_unix_format, \
    exclude_obj_callback, compare_directories_and_collate_difference, validate_roles_and_environment, run_in_client, \
    execute_get, execute_post, is_response_ok, execute_put, get_object_from_db_with_name, check_all_apps_in_cluster, \
    clean_up_db

log = logging.getLogger(__name__)

setting = get_settings()


@step("I hit the {endpoint} to get all {model_type}")
def step_impl(context, endpoint, model_type):
    file_path, final_url = get_url_and_file_path(endpoint)
    c_headers = context.c_headers
    response = run_in_client(execute_get, c_headers, final_url)
    context.resp = response


@step("I have a pipeline access token")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    setting.AZURE_CLIENT_ID = "someclientId"
    setting.AZURE_TENANT_ID = "sometenantid"
    payload_for_access_token = {
        "aud": setting.AZURE_CLIENT_ID,
        "iss": f"https://login.microsoftonline.com/{setting.AZURE_TENANT_ID}/v2.0",
        "aio": "ASQA2/8TAAAA/622c0+f+ztllVyrd9eWw0J1ht0npvnZQL/SNl+Q8VM=",
        "azp": setting.AZURE_CLIENT_ID,
        "azpacr": "1",
        "ver": "2.0",
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'kid': 'secret_key',
    }
    secret_key = 'my_secret_key'
    # Create the JWT token
    headers = {'kid': secret_key}
    access_token = jwt.encode(payload_for_access_token, secret_key, algorithm='HS256', headers=headers)
    c_headers = common_headers(context)
    c_headers[APP_SERVICE_ACCESS_TOKEN_HEADER] = access_token
    setting.WEBSITE_AUTH_ENABLED = True
    context.c_headers = c_headers


@step("I am part of below groups")
def setup_role(context):
    groups = []
    for row in context.table:
        groups.append(row["group"])

    payload_for_access_token = {
        'user_id': 123,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iss': 'bdd-test',
        'audience': 'bdd-test-execution',
        'kid': 'secret_key',
        'name': 'testing user'
    }

    # Define the secret key to sign the JWT token
    secret_key = 'my_secret_key'
    # Create the JWT token
    headers = {'kid': secret_key}
    access_token = jwt.encode(payload_for_access_token, secret_key, algorithm='HS256', headers=headers)
    payload_for_id_token = payload_for_access_token
    payload_for_id_token['groups'] = groups
    payload_for_id_token['email'] = "bdd-buddy@invaliddomain.com"
    id_token = jwt.encode(payload_for_access_token, secret_key, algorithm='HS256', headers=headers)
    c_headers = common_headers(context)
    c_headers[APP_SERVICE_ACCESS_TOKEN_HEADER] = access_token
    c_headers[APP_SERVICE_ID_TOKEN_HEADER] = id_token
    setting.WEBSITE_AUTH_ENABLED = True
    context.c_headers = c_headers


@then("I should get {model_type} with names as below")
def step_impl(context, model_type):
    responses: NamespaceListResponse = NamespaceListResponse.parse_obj(context.resp.json())
    response_set = set(map(lambda res: res.name, responses.items))
    names_set = set(map(lambda row: row["name"], context.table))
    assert names_set.difference(response_set) != 0, " Failed: Found {}, required {}".format(str(response_set),
                                                                                            str(names_set))


@step("The response should have below attribute")
def step_impl(context):
    flattened_object = utils.flatten_object(context.resp.json())
    for row in context.table:
        value_in_object = flattened_object[row["attribute_name"]]
        assert value_in_object == row["value"], "Expected {}, got {}".format(row["value"], value_in_object)


@step("I hit the {endpoint} to get same {model_type} with id")
def validate_get_by_id(context, endpoint, model_type):
    c_headers = context.c_headers
    resp = run_in_client(execute_get, c_headers, f"/{endpoint}/{context.id}")
    context.resp = resp


@when('I hit the {endpoint} to create a {model_type} with below data')
def step_when(context, endpoint, model_type):
    context.type = model_type
    if getattr(context, "resp", None) is not None:
        context.resp = None
    for row in context.table:
        data = row.get("data", json.dumps(utils.convert_row_to_dict(row)))
        c_headers = context.c_headers
        resp = run_in_client(execute_post, c_headers, data, endpoint)
        context.resp = resp
        if is_response_ok(resp.status_code):
            context.id = resp.json()["id"]


@when('I hit the {endpoint} to put a {model_type} with below data')
def put_request(context, endpoint, model_type):
    context.type = model_type
    if getattr(context, "resp", None) is not None:
        context.resp = None

    if getattr(context, "id", None) is not None:
        endpoint = endpoint.replace("{id}", context.id)

    for row in context.table:
        data = utils.convert_row_to_dict(row)
        c_headers = context.c_headers
        resp = run_in_client(execute_put, c_headers, data, endpoint)
        context.resp = resp


@step("The header should have {header_attribute}")
def step_impl(context, header_attribute):
    response = context.resp
    header_value = response.headers[header_attribute]
    assert header_value is not None, "Header {} is not found".format(header_attribute)


@then('The response status code should be {status_code}')
def step_then(context, status_code):
    assert context.resp.status_code == int(status_code), "Expected {} got {}".format(status_code,
                                                                                     context.resp.status_code)


@step('The response should have id')
def response_should_have_id(context):
    assert context.resp.json()["id"] is not None


@then("The response to create a {model_type} should be same as data from {json_file}")
def response_similar_to_json(context, model_type, json_file):
    response_json = sorted(context.resp.json())
    file_path = converted_file_path(json_file, model_type)
    with open(file_path, 'r') as f:
        data = sorted(json.load(f))
        difference = DeepDiff(response_json, data, ignore_order=True, ignore_private_variables=True,
                              exclude_obj_callback=exclude_obj_callback)
        diff = len(difference.keys())
        assert diff == 0, "FAILED: expected {} got {} ".format(response_json, data)


@then(
    "The {model_type} should have been created with this criteria {filter_attribute} having id as received in response")
def validate_type_created_with_criteria(context, model_type: str, filter_attribute: str):
    loop = ready_db_object_for_query(context)  # Is there a better way?????????
    db_table_model = models.get_model(model_type)
    # TODO: One target is one deployment????
    objects = loop.run_until_complete(
        db_table_model.find(getattr(db_table_model, filter_attribute) == context.id).to_list())
    context.deployment_objects = objects
    assert len(objects) != 0


@step("I have {model_type} created in DB with below")
def step_impl(context, model_type):
    loop = ready_db_object_for_query(context)  # Is there a better way?????????
    from app.core.models.clusters import Cluster
    db_table_model: Cluster = models.get_model(model_type)
    for row in context.table:
        row_in_dict = utils.convert_row_to_dict(row)
        record = db_table_model(id=str(uuid4()), **row_in_dict)
        saved_object = loop.run_until_complete(record.save())
        assert saved_object is not None, "Failed: Object could not be saved into {}".format(model_type)


@step("The {model_type} with below name should be created having status {onboard_status}")
def validate_model_with_status(context, model_type, onboard_status):
    loop = ready_db_object_for_query(context)
    for row in context.table:
        db_object = get_object_from_db_with_name(loop, model_type, row["name"])
        assert db_object is not None, "FAILED: type {} not found".format(model_type)
        assert db_object.onboard_status == onboard_status, "FAILED: expected {} got {}".format(
            db_object.onboard_status, onboard_status)


@then("The {model_type} with name {name} should be created")
def validate_type_in_db_with_filter(context, model_type, name):
    loop = ready_db_object_for_query(context)
    db_object = get_object_from_db_with_name(loop, model_type, name)
    assert db_object is not None, "FAILED: type {} not found".format(model_type)


@then("The below applications are present on specified clusters")
def validate_cluster_state(context):
    loop = ready_db_object_for_query(context)  # Is there a better way?????????
    for row in context.table:
        cluster_names = row["cluster_name"].split(",")
        for cluster_name in cluster_names:
            expected_app_names = set(row["comma_seperated app_name"].split(","))
            app_names, difference = check_all_apps_in_cluster(cluster_name, expected_app_names, loop)
            assert len(difference) == 0, "FAILED: expected app {} found {}".format(expected_app_names,
                                                                                   app_names)


@then("There is no application on specified clusters")
def validate_cluster_state(context):
    loop = ready_db_object_for_query(context)
    for row in context.table:
        cluster_names = row["cluster_name"].split(",")
        for cluster_name in cluster_names:
            app_names, difference = check_all_apps_in_cluster(cluster_name, None, loop)
            assert app_names is None


@step("The cluster for below selector should reflect only applications selected as below")
def validate_cluster_and_application(context):
    loop = ready_db_object_for_query(context)
    for row in context.table:
        row_to_dict = utils.convert_row_to_dict(row)
        clusters: list[Cluster] = loop.run_until_complete(get_clusters_by_selector(row_to_dict["cluster_selector"]))
        expected_app_names: list[Application] = loop.run_until_complete(
            get_apps_by_selector(row_to_dict["app_selector"]), None)
        for cluster in clusters:
            app_names, difference = check_all_apps_in_cluster(cluster.name,
                                                              set(map(lambda app: app.name, expected_app_names)), loop)
            assert len(
                difference) == 0, "FAILED: expected app {} found {} while checking by cluster select {} and app selector {}".format(
                expected_app_names,
                app_names, row_to_dict["cluster_selector"], row_to_dict["app_selector"])


@then("The deployment should have details as per below table")
def validate_deployment(context):
    deployments = context.deployment_objects
    deployment: Deployment = deployments[0]
    for row in context.table:
        operation = row["operation"]
        app_name = set(row["comma_separated_app_name"].split(","))
        cluster_name = row["cluster_name"]
        for mapping_key in deployment.deployment_mappings:
            deployment_state: DeploymentState = deployment.deployment_mappings[mapping_key]
            application_response: ApplicationResponse = getattr(deployment_state, operation)
            # Do we check other properties
            app_names = set(map(lambda app_response: app_response.name, application_response))
            difference = app_name.difference(app_names)
            assert len(difference) == 0, "FAILED: expected app {} found {}".format(app_name,
                                                                                   application_response.name)
            cluster_context: ClusterResponse = deployment_state.cluster_context
            assert cluster_context.name == cluster_name, "FAILED: expected cluster {} found {}".format(cluster_name,
                                                                                                       cluster_context.name)


@step("There should be no manifest created")
def check_no_manifest(context):
    path = tests.common.common.commit_dir_path
    assert len(os.listdir(path)) == 0, "Manifests were created"


@step("The manifests should have been created exactly as {source_dir}")
def check_directories(context, source_dir):
    test_data_dir = f"tests/testdata/{source_dir}"
    convert_unix_format(tests.common.common.commit_dir_path)
    log.info(f"test data dir {test_data_dir} and commit dir {tests.common.common.commit_dir_path}")
    convert_unix_format(test_data_dir)
    difference = compare_directories_and_collate_difference(tests.common.common.commit_dir_path, test_data_dir)
    assert len(difference) == 0, f"manifest generation mismatch {difference}"


@step("I have manifest checked out from {source_dir} at {checkout_dir}")
def manifest_checkout(context, source_dir, checkout_dir):
    tests.common.common.checkout_dir_path = f"tests/testdata/{source_dir}"
    print(f"checkout dir path {tests.common.common.checkout_dir_path}")


@step("I have access and id token")
def step_impl(context):
    assert context.c_headers[APP_SERVICE_ACCESS_TOKEN_HEADER] is not None, "ERROR: ACCESS_TOKEN_HEADER not found"
    assert context.c_headers[APP_SERVICE_ID_TOKEN_HEADER] is not None, "ERROR: ID_TOKEN_HEADER not found"


@then("User has {expected_roles} role against {environments} environment")
def step_impl(context, expected_roles, environments):
    def validate_and_assert(entitled_roles):
        assert len(entitled_roles) != 0, "ERROR: ENTITLED_ROLE not found"

    loop = ready_db_object_for_query(context)
    loop.run_until_complete(validate_roles_and_environment(context, expected_roles, environments, validate_and_assert))


@then("User does not have {expected_roles} role against {environments} environment")
def step_impl(context, expected_roles, environments):
    def validate_and_assert(entitled_roles):
        assert len(entitled_roles) == 0, "ERROR: ENTITLED_ROLE found should have been missing"

    try:
        loop = ready_db_object_for_query(context)
        func_succeeded = loop.run_until_complete(
            validate_roles_and_environment(context, expected_roles, environments, validate_and_assert))
    except UnAuthorizedException as e:  # In case if it is role mismatch the error will come here
        assert True
        return
    assert func_succeeded, "Error: Mismatched in roles"  # In case if it is environment mismatch. Environment is
    # application concern


@then("There should be {number_of_items} items in response")
def step_impl(context, number_of_items):
    response_json = context.resp.json()
    assert len(response_json["items"]) == int(number_of_items), "Error in {}. Expected {} got {}".format(
        context.scenario.name, number_of_items, len(response_json["items"]))


@step("database is cleaned up")
def step_impl(context):
    clean_up_db(None)
