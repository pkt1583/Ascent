import json
from logging import getLogger
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq
from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.params import Depends

from app.api.endpoints import ValidateAndReturnUser
from app.core.auth.user import User
from app.core.config import get_settings
from app.core.models.namespaces import Namespace
from app.core.schemas.namespaces import (
    NamespaceListResponse,
    NamespaceRequest,
    NamespaceResponse,
)
from app.core.services.namespaces import get_all_namespaces
from app.utils.common import init_common_model_attributes
from app.utils.constants import (
    CREATE_NAMESPACES_ROUTE_SUMMARY,
    GET_ALL_NAMESPACES_ROUTE_SUMMARY,
    GET_NAMESPACE_BY_ID_ROUTE_SUMMARY,
)

router = APIRouter()

log = getLogger(__name__)

settings = get_settings()


@router.post(
    "",
    response_model=NamespaceResponse,
    response_model_by_alias=False,
    status_code=201,
    response_model_exclude_none=True,
    summary=CREATE_NAMESPACES_ROUTE_SUMMARY,
)
async def create_namespaces(
        body: NamespaceRequest, request: Request, response: Response,
        user: User = Depends(ValidateAndReturnUser(expected_roles=[settings.ADMIN_ROLE_NAME]))
) -> NamespaceResponse:
    """
    Creates a new namespace
    Args:
        body: Namespace object to be created
        request: Request
        response: HTTP Response (status code - 201 if successful, 409 if namespace already exists)
        user: User (expected role - admin)
    Returns:
        NamespaceResponse: Namespace object created, if successful
    """
    log.debug(
        f"Received POST request for create_Namespaces with payload :  \
        {json.dumps(body.json())}"
    )
    log.info("Checking if namespace with Name {body.name} already exists")
    namespace_obj = await Namespace.find_one(Namespace.name == str(body.name))

    if namespace_obj:
        log.debug(f"namespace with Name {body.name} already exists")
        response.status_code = status.HTTP_409_CONFLICT
        return namespace_obj
    namespace_obj = Namespace(id=str(uuid4()), **body.dict())
    namespace_obj = init_common_model_attributes(namespace_obj, user)
    return await namespace_obj.save()


@router.get(
    "",
    response_model=NamespaceListResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_ALL_NAMESPACES_ROUTE_SUMMARY,
)
async def get_namespaces(
        user: User = Depends(
            ValidateAndReturnUser(expected_roles=[settings.READER_ROLE_NAME]))) -> NamespaceListResponse:
    """
    Returns all Namespaces
    Args:
        user: User (expected role - reader)
    Returns:
        NamespaceListResponse: List of all Namespaces
    """
    log.debug("Received GET request for all Namespaces")
    namespaces = await get_all_namespaces(user)
    return NamespaceListResponse(
        items=namespaces,
    )


@router.get(
    "/{namespaceId}",
    response_model=NamespaceResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_NAMESPACE_BY_ID_ROUTE_SUMMARY,
)
async def get_namespace_by_id(namespaceId: str, user: User = Depends(ValidateAndReturnUser(expected_roles=[
    settings.READER_ROLE_NAME]))) -> NamespaceResponse:
    """
    Returns a namespace by ID
    Args:
        namespaceId: ID of the namespace to be returned
        user: User (expected role - reader)
    Returns:
        NamespaceResponse: Namespace object with the given ID
    Exceptions:
        HTTPException: 404 - if namespace with the given ID is not found
    """
    log.debug(f"Received GET Request for namespace By Id : {namespaceId}")
    namespace_obj = await Namespace.find_one(Eq(Namespace.id, namespaceId))
    if not namespace_obj:
        log.warning(f"namespace ID : {namespaceId} not Found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"namespace with ID: {namespaceId} not found."
        )
    if user.is_plat_admin():
        authorized_envs: list[str] = await user.role_collection.get_environments()
        # assuming that the pattern is xxx-{env}-{role} xx can be anything. Even it an contain "-"
        env_by_group = {group.split(settings.GROUP_NAME_SEPARATOR)[-2] for group in namespace_obj.group}
        if len(env_by_group.intersection(authorized_envs)) != 0:
            return namespace_obj
    role_in_group_format = user.role_collection.get_role_in_namespace_group_format()
    if len(set(namespace_obj.group).intersection(role_in_group_format)) != 0:
        return namespace_obj

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail=f"namespace with {namespaceId} not found."
    )
