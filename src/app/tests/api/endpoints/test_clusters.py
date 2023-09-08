import pytest
from fastapi.testclient import TestClient
from app.app import app
from logging import getLogger
from beanie import init_beanie
from app.core.models.clusters import Cluster
from app.core.models.models import __beanie_models__
from mongomock_motor import AsyncMongoMockClient
from app.core.config import get_settings
from app.core.schemas.clusters import ClusterRequest, ClusterListResponse, ClusterResponse
from app.app import get_settings


log = getLogger(__name__)

client = TestClient(app=app)
settings = get_settings()
version = settings.VERSION


@pytest.fixture()
async def resource(cluster_post_valid_payload_data01):
    app = AsyncMongoMockClient()
    await init_beanie  (
        document_models=[Cluster], database=app.get_database(name="contoso")
    )
    client.post(
        f"{version}/clusters", json=cluster_post_valid_payload_data01
    )

@pytest.mark.asyncio
async def test_create_cluster_with_no_validation_errors(resource, cluster_post_valid_payload_data01):
    await resource
    response = client.post(f"{version}/clusters",json=cluster_post_valid_payload_data01)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_cluster_with_missing_required_data(resource,cluster_payload_missing_required):
    await resource
    response = client.post(f"{version}/clusters",json=cluster_payload_missing_required)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_cluster_duplicate_errors(resource, cluster_post_valid_payload_data02):
    await resource
    #create a cluster and create another cluster with same data
    client.post(f"{version}/clusters",json=cluster_post_valid_payload_data02)
    response = client.post(f"{version}/clusters",json=cluster_post_valid_payload_data02)    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_clusters(resource):
    await resource
    #get the clusters
    response = client.get(f"{version}/clusters")
    assert response.status_code == 200



@pytest.mark.asyncio
async def test_get_clusters_by_id(resource,cluster_post_valid_payload_data01):
    await resource
    #add a cluster
    response = client.post(f"{version}/clusters",json=cluster_post_valid_payload_data01)
    # get the id of cluster from response
    clusterId = response.json()['id']
    #get the clusters
    getResponse = client.get(f"{version}/clusters/{clusterId}")
    assert getResponse.status_code == 200
    assert getResponse.json()["id"] == clusterId


@pytest.mark.asyncio
async def test_create_cluster_with_invalid_data(resource, cluster_post_in_valid_payload):
    await resource
    # create a cluster with Invalid data
    response = client.post(f"{version}/clusters",json=cluster_post_in_valid_payload)  
    assert response.status_code == 422