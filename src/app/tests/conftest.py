import pytest
from app.tests.test_data.clusters import *
from app.tests.test_data.applications import *
from app.tests.test_data.namespaces import *
from app.tests.test_data.targetpolicies import *


@pytest.fixture(autouse=True)
def cluster_post_valid_payload_data01():
    return cluster_post_valid_payload_raw_data01

@pytest.fixture(autouse=True)
def cluster_post_valid_payload_data02():
    return cluster_post_valid_payload_raw_data02

@pytest.fixture(autouse=True)
def cluster_payload_missing_required():
    return cluster_payload_missing_required_data


@pytest.fixture(autouse=True)
def cluster_post_in_valid_payload():
    return cluster_post_in_valid_payload_data

@pytest.fixture(autouse=True)
def namespace_post_valid_payload_data01():
    return namespace_post_valid_payload_raw_data01

@pytest.fixture(autouse=True)
def namespace_post_valid_payload_data02():
    return namespace_post_valid_payload_raw_data02

@pytest.fixture(autouse=True)
def namespace_payload_missing_required():
    return namespace_payload_missing_required_data


@pytest.fixture(autouse=True)
def namespace_post_in_valid_payload():
    return namespace_post_in_valid_payload_data

### Application Test config

@pytest.fixture(autouse=True)
def app_post_valid_payload_data01():
    return app_post_valid_payload_raw_data01

@pytest.fixture(autouse=True)
def app_post_valid_payload_data02():
    return app_post_valid_payload_raw_data02

@pytest.fixture(autouse=True)
def app_payload_missing_required():
    return app_payload_missing_required_data


@pytest.fixture(autouse=True)
def app_post_in_valid_payload():
    return app_post_in_valid_payload_data
