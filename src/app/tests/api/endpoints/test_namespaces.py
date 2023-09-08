import pytest
from fastapi.testclient import TestClient
from app.app import app
from logging import getLogger
from beanie import init_beanie
from app.core.models.namespaces import Namespace
from mongomock_motor import AsyncMongoMockClient
from app.core.config import get_settings
from app.core.schemas.namespaces import NamespaceRequest, NamespaceResponse, NamespaceListResponse
from app.app import get_settings


log = getLogger(__name__)

client = TestClient(app=app)
settings = get_settings()
version = settings.VERSION


@pytest.fixture()
async def resource(namespace_post_valid_payload_data01):
    app = AsyncMongoMockClient()
    await init_beanie  (
        document_models=[Namespace], database=app.get_database(name="contoso")
    )
    client.post(
        f"{version}/namespaces", json=namespace_post_valid_payload_data01
    )

@pytest.mark.asyncio
async def test_create_namespace_with_no_validation_errors(resource, namespace_post_valid_payload_data01):
    await resource
    response = client.post(f"{version}/namespaces",json=namespace_post_valid_payload_data01)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_namespace_with_missing_required_data(resource,namespace_payload_missing_required):
    await resource
    response = client.post(f"{version}/namespaces",json=namespace_payload_missing_required)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_cluster_duplicate_errors(resource, namespace_post_valid_payload_data02):
    await resource
    #create a namespace and create another namespace with same data
    client.post(f"{version}/namespaces",json=namespace_post_valid_payload_data02)
    response = client.post(f"{version}/namespaces",json=namespace_post_valid_payload_data02)    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_namespaces(resource):
    await resource
    #get the namespaces
    response = client.get(f"{version}/namespaces")
    assert response.status_code == 200



@pytest.mark.asyncio
async def test_get_namespace_by_id(resource,namespace_post_valid_payload_data01):
    await resource
    #add a cluster
    response = client.post(f"{version}/namespaces",json=namespace_post_valid_payload_data01)
    # get the id of namespace from response
    namespaceId = response.json()['id']
    #get the namespaces
    getResponse = client.get(f"{version}/namespaces/{namespaceId}")
    assert getResponse.status_code == 200
    assert getResponse.json()["id"] == namespaceId


@pytest.mark.asyncio
async def test_create_namespace_with_invalid_data(resource, namespace_post_in_valid_payload):
    await resource
    # create a namespace with Invalid data
    response = client.post(f"{version}/namespaces",json=namespace_post_in_valid_payload)  
    assert response.status_code == 422