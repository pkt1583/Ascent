import filecmp
import fileinput
import json
import logging
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import yaml
from requests_toolbelt import sessions
from starlette.testclient import TestClient

from app import app
from app.api.endpoints import ValidateAndReturnUser
from app.core.auth.http.appservice import AppServiceBasedTokenProvider
from app.core.auth.token_service import DefaultTokenService
from app.core.config import get_settings
from app.core.models import models
from app.core.models.clusterstate import ClusterState
from app.core.schemas.applications import ApplicationRequest
from app.core.schemas.clusters import ClusterRequest
from app.core.schemas.namespaces import NamespaceRequest
from app.core.schemas.targetpolicies import TargetPolicyRequest
from app.utils.constants import APP_SERVICE_ACCESS_TOKEN_HEADER, APP_SERVICE_ID_TOKEN_HEADER
from tests import environment
from tests.common.common import ready_db_object_for_query

settings = get_settings()

log = logging.getLogger(__name__)

token_service = DefaultTokenService(token_provider=AppServiceBasedTokenProvider())

schema_map = {"application": ApplicationRequest, "cluster": ClusterRequest, "namespace": NamespaceRequest,
              "targetpolicy": TargetPolicyRequest}
def create_nested_dict(nested_dict, keys, value):
    current_dict = nested_dict
    for key in keys[:-1]:
        if key not in current_dict:
            current_dict[key] = {}
        current_dict = current_dict[key]
    current_dict[keys[-1]] = value


def convert_row_to_dict(row):
    row_dict = {}
    for k, v in row.items():
        nested_keys = k.split('.')
        nested_dict = row_dict
        for nested_key in nested_keys[:-1]:
            nested_dict.setdefault(nested_key, {})
            nested_dict = nested_dict[nested_key]

        last_key = nested_keys[-1]
        if ',' in v:
            temp_arr = []
            for element in v.split(','):
                if len(element.strip()) != 0:
                    temp_arr.append(element)
            nested_dict[last_key] = temp_arr
        else:
            nested_dict[last_key] = v

    return row_dict

def get_json_from_dict(my_dict) -> str:
    nested_dict = {}
    for key, value in my_dict.items():
        keys = key.split(".")
        create_nested_dict(nested_dict, keys, value)
    json_data = json.dumps(nested_dict)
    return json_data


def is_same_content(file1, file2, ignored_nodes) -> bool:
    with open(file1, "r") as f1:
        data1 = yaml.safe_load(f1)
    with open(file2, "r") as f2:
        data2 = yaml.safe_load(f2)
    for node in ignored_nodes:
        remove_node(data1, node)
        remove_node(data2, node)
    if data1 == data2:
        return True
    else:
        return False


def remove_node(data, node):
    if isinstance(data, dict):
        if node in data:
            del data[node]
        for key, value in data.items():
            remove_node(value, node)
    elif isinstance(data, list):
        for item in data:
            remove_node(item, node)


def get_url_and_file_path(endpoint, json_file=None, type=None):
    final_url = f"/{endpoint}"
    if json_file is None:
        return None, final_url
    file_path = converted_file_path(json_file, type)
    return file_path, final_url


def converted_file_path(json_file, type):
    file_path = os.path.join(Path(__file__).parent, "../testdata", type, json_file)
    return file_path


def convert_unix_format(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            with fileinput.FileInput(path, inplace=True) as f:
                for line in f:
                    print(line.replace('\r\n', '\n'), end='')


def _collate_comparison_issues(comparison: filecmp.dircmp):
    comparison_issues = []
    if comparison.left_only:
        comparison.left_only.sort()
        comparison_issues.append(f"Only in: {comparison.left}, :, {comparison.left_only}")
    if comparison.right_only:
        comparison.right_only.sort()
        comparison_issues.append(f"Only in: {comparison.right}, :, {comparison.right_only}")
    if comparison.diff_files:
        comparison.diff_files.sort()
        for file in comparison.diff_files:
            if not is_same_content(os.path.join(comparison.left, file), os.path.join(comparison.right, file),
                                   ["targetId"]):
                comparison_issues.append(f"Differing files : {comparison.diff_files}")
    return comparison_issues


def _check_for_difference_recursive(comparison: filecmp.dircmp, diff):  # Report on self and subdirs recursively
    comparison_report = _collate_comparison_issues(comparison)
    if len(comparison_report) != 0:
        diff.append(comparison_report)
    for subdirectory in comparison.subdirs.values():
        _check_for_difference_recursive(subdirectory, diff)
    return diff


def compare_directories_and_collate_difference(directory1, directory2) -> int:
    dir_comparison: filecmp.dircmp = filecmp.dircmp(directory1, directory2)
    return _check_for_difference_recursive(dir_comparison, [])


def exclude_obj_callback(obj, path):
    if obj == "id" or obj == "created_on" or obj == "updated_on" or obj == "_id":
        return True
    return False


async def validate_roles_and_environment(context, expected_roles, environments, func):
    func_succeded = False
    u_user = ValidateAndReturnUser(expected_roles=expected_roles.split(","))
    mock_request = MagicMock()
    mock_request.headers = {APP_SERVICE_ACCESS_TOKEN_HEADER: context.c_headers[APP_SERVICE_ACCESS_TOKEN_HEADER],
                            APP_SERVICE_ID_TOKEN_HEADER: context.c_headers[APP_SERVICE_ID_TOKEN_HEADER]}
    user = await token_service.decode_and_check_authorization(u_user.expected_roles, request=mock_request)
    for expected_role in expected_roles.split(","):
        func_succeded = True
        for env in environments.split(","):
            entitled_roles = user.role_collection.get_rbac_by_env_and_type(env=env, role_type=expected_role)
            func(entitled_roles)
    return func_succeded



def flatten_object(obj, prefix=''):
    flattened: dict[str | Any, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                flattened.update(flatten_object(value, f"{prefix}{key}."))
            else:
                flattened[f"{prefix}{key}"] = value
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                flattened.update(flatten_object(value, f"{prefix}{index}."))
            else:
                flattened[f"{prefix}{index}"] = value
    else:
        flattened[prefix[:-1]] = obj
    return flattened


def run_in_client(fn, *args):
    os.environ['no_proxy'] = 'localhost'
    if environment.is_running_end_to_end:
        client = sessions.BaseUrlSession(base_url=environment.base_url_for_end_to_end)
        return fn(client, *args)
    else:
        with TestClient(app.app, raise_server_exceptions=False) as client:
            return fn(client, *args)


def execute_get(client, c_headers, endpoint):
    resp = client.get(endpoint, headers=c_headers, cookies=None)
    return resp


def execute_post(client, c_headers, data, endpoint):
    resp = client.post(f"/{endpoint}", headers=c_headers, cookies=None, data=data)
    return resp


def execute_put(client, c_headers, data, endpoint):
    resp = client.put(f"/{endpoint}", headers=c_headers, cookies=None, json=data)
    return resp

def is_response_ok(status_code):
    return 200 <= status_code < 300


def clean_up_db(db_name):
    loop = ready_db_object_for_query()
    for k, v in models.__beanie_models__.items():
        log.info("Deleting all records from %s collection", k)
        result = loop.run_until_complete(v.delete_all())
        log.info("Deleted %d records from %s collection", result.deleted_count, k)


def get_object_from_db_with_name(loop, model_type, name):
    # Is there a better way?????????
    dbmodel = models.get_model(model_type)
    db_object = loop.run_until_complete(dbmodel.find_one({'name': {'$eq': name}}))
    return db_object


def check_all_apps_in_cluster(cluster_name, expected_app_names, loop):
    cluster_state = loop.run_until_complete(ClusterState.find_one({'cluster.name': {'$eq': cluster_name}}))
    applications_in_cluster = cluster_state.applications
    if expected_app_names is None:
        if len(applications_in_cluster) != 0:
            raise Exception("Expected no application but found {} applications", applications_in_cluster)
        else:
            return expected_app_names, 0
    app_names = set(map(lambda application: application.name, applications_in_cluster))
    difference = app_names.symmetric_difference(expected_app_names)
    return app_names, difference
