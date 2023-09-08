import pytest
from fastapi.testclient import TestClient
from app.app import app
from logging import getLogger
from beanie import init_beanie
from app.core.models.applications import Application
from mongomock_motor import AsyncMongoMockClient
from app.core.config import get_settings
from app.core.schemas.applications import ApplicationRequest, ApplicationListResponse, ApplicationResponse
from app.app import get_settings


log = getLogger(__name__)

client = TestClient(app=app)
settings = get_settings()
version = settings.VERSION


@pytest.fixture()
async def resource(app_post_valid_payload_data01):
    app = AsyncMongoMockClient()
    await init_beanie  (
        document_models=[Application], database=app.get_database(name="contoso")
    )
    client.post(
        f"{version}/applications", json=app_post_valid_payload_data01
    )

@pytest.mark.asyncio
async def test_create_app_with_no_validation_errors(resource, app_post_valid_payload_data02):
    await resource
    response = client.post(f"{version}/applications",json=app_post_valid_payload_data02)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_app_with_missing_required_data(resource,app_payload_missing_required):
    await resource
    response = client.post(f"{version}/applications",json=app_payload_missing_required)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_app_duplicate_errors(resource, app_post_valid_payload_data02):
    await resource
    #create an app and create another app with same data
    client.post(f"{version}/applications",json=app_post_valid_payload_data02)
    response = client.post(f"{version}/aplications",json=app_post_valid_payload_data02)    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_applications(resource):
    await resource
    #get the applications
    response = client.get(f"{version}/applications")
    assert response.status_code == 200



@pytest.mark.asyncio
async def test_getApplicationsById(resource,app_post_valid_payload_data01):
    await resource
    #add an app
    response = client.post(f"{version}/applications",json=app_post_valid_payload_data01)
    # get the id of application from response
    appId = response.json()['id']
    #get the application
    getResponse = client.get(f"{version}/applications/{appId}")
    assert getResponse.status_code == 200
    assert getResponse.json()["id"] == appId


@pytest.mark.asyncio
async def test_createApplicationWithInvalidData(resource, app_post_in_valid_payload):
    await resource
    # create an application with Invalid data
    response = client.post(f"{version}/applications",json=app_post_in_valid_payload)  
    assert response.status_code == 422