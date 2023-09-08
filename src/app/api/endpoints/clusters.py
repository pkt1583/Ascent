import json
from logging import getLogger
from uuid import uuid4

from beanie.odm.operators.find.comparison import In
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends

from app.api.endpoints import ValidateAndReturnUser
from app.core.auth.user import User
from app.core.config import get_settings
from app.core.models.clusters import Cluster
from app.core.schemas.clusters import (
    ClusterListResponse,
    ClusterRequest,
    ClusterResponse,
)
from app.core.services import clusters
from app.core.services.onboarder import ClusterOnboarder
from app.utils.common import init_common_model_attributes
from app.utils.constants import (
    CREATE_CLUSTER_ROUTE_SUMMARY,
    GET_ALL_CLUSTERS_ROUTE_SUMMARY,
    GET_CLUSTER_BY_ID_ROUTE_SUMMARY,
)
from app.utils.enums import OnboardStatus

router = APIRouter()

log = getLogger(__name__)
settings = get_settings()


@router.post(
    "",
    response_model=ClusterResponse,
    response_model_by_alias=False,
    status_code=201,
    response_model_exclude_none=True,
    summary=CREATE_CLUSTER_ROUTE_SUMMARY,
)
async def create_cluster(
        cluster_request: ClusterRequest, request: Request, response: Response,
        user: User = Depends(ValidateAndReturnUser(expected_roles=[
            settings.ADMIN_ROLE_NAME]))
) -> ClusterResponse:
    """
    Creates a new cluster
    Args:
        cluster_request: Cluster object to be created
        request: Request
        response: HTTP Response (status code - 201 if successful, 409 if cluster already exists, 500 if onboard fails)
        user: User (expected role - admin)
    Returns:
        ClusterResponse: Cluster object created, if successful
    Exceptions:
        HTTPException: 403 if user is not authorized to create cluster for the environment, 500 if onboard fails, 409 if cluster already exists,
        403 if user is not authorized to create cluster for the environment
    """
    log.debug(
        f"Received POST request for create_cluster with payload :  \
        {json.dumps(cluster_request.json())}"
    )

    entitled_envs = await user.role_collection.get_environments()
    if cluster_request.environment in entitled_envs:
        log.debug(f"Checking if cluster with Name {cluster_request.name} already exists")
        cluster_obj = await Cluster.find_one(Cluster.name == str(cluster_request.name),
                                             Cluster.onboard_status != OnboardStatus.FAILURE)

        if cluster_obj:
            log.debug(f"cluster with Name {cluster_request.name} already exists")
            response.status_code = status.HTTP_409_CONFLICT
            return cluster_obj

        log.debug("Creating cluster Object in DB")

        cluster_obj = Cluster(id=str(uuid4()), **cluster_request.dict())
        cluster_obj = init_common_model_attributes(cluster_obj, user)
        cluster_obj.onboard_status = await ClusterOnboarder(cluster_obj, user).onboard()

        await cluster_obj.save()
        if cluster_obj.onboard_status == OnboardStatus.FAILURE:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return cluster_obj
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="User {} is not authorized to create cluster for env {}".format(user.name,
                                                                                               cluster_request.environment))


@router.get(
    "",
    response_model=ClusterListResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_ALL_CLUSTERS_ROUTE_SUMMARY,
)
async def get_clusters(query: str = None, user: User = Depends(ValidateAndReturnUser(expected_roles=[
    settings.READER_ROLE_NAME]))) -> ClusterListResponse:
    """
    Returns all clusters
    Args:
        query: Query string
        user: User (expected role - reader)
    Returns:
        ClusterListResponse: List of all clusters
    """
    log.debug("Received GET request for all Clusters")

    cluster_list = await clusters.fetch_clusters(query,
                                                 In(Cluster.environment, await user.role_collection.get_environments()))
    return ClusterListResponse(
        items=cluster_list,
    )


@router.get(
    "/{id}",
    response_model=ClusterResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_CLUSTER_BY_ID_ROUTE_SUMMARY,
)
async def get_cluster_by_id(id: str, user: User = Depends(ValidateAndReturnUser(expected_roles=[
    settings.READER_ROLE_NAME]))) -> ClusterResponse:
    """
    Returns cluster by Id
    Args:
        id: Cluster Id
        user: User (expected role - reader)
    Returns:
        ClusterResponse: Cluster object (if found)
    Exceptions:
        HTTPException: 404 if cluster not found
    """
    log.debug(f"Received GET Request for cluster By Id : {id}")
    cluster_obj = await Cluster.find_one(Cluster.id == id, In(Cluster.environment,
                                                              await user.role_collection.get_environments()))
    if not cluster_obj:
        log.warning(f"ClusterId: {id} not Found.")
        raise HTTPException(
            status_code=404,
            detail=f"Cluster with {id} not found.",
        )
    return cluster_obj
