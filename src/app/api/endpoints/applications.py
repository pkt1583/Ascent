import json
from logging import getLogger
from uuid import uuid4

from fastapi import APIRouter, Request, Response, HTTPException, status, Depends

from app.api.endpoints import ValidateAndReturnUser
from app.core.auth.user import User
from app.core.config import get_settings
from app.core.models.applications import Application
from app.core.models.namespaces import Namespace
from app.core.schemas.applications import (
    ApplicationListResponse,
    ApplicationRequest,
    ApplicationResponse,
)
from app.core.services.applications import filter_apps_not_authorized, fetch_applications
from app.core.services.namespaces import is_part_of_namespace_group
from app.core.services.onboarder import ApplicationOnboarder
from app.utils.common import init_common_model_attributes
from app.utils.constants import (
    CREATE_APPLICATION_ROUTE_SUMMARY,
    GET_ALL_APPLICATIONS_ROUTE_SUMMARY,
    GET_APPLICATION_BY_ID_ROUTE_SUMMARY
)
from app.utils.enums import OnboardStatus

router = APIRouter()
log = getLogger(__name__)
settings = get_settings()


@router.post(
    "",
    response_model=ApplicationResponse,
    response_model_by_alias=False,
    status_code=201,
    summary=CREATE_APPLICATION_ROUTE_SUMMARY,
    response_model_exclude_none=True,
)
async def create_application(
        application_request: ApplicationRequest, request: Request, response: Response,
        user: User = Depends(ValidateAndReturnUser(expected_roles=[settings.CONTRIBUTOR_ROLE_NAME]))
) -> ApplicationResponse:
    """
    Creates a new application
    Args:
        application_request: Application object to be created
        request: Request
        response: HTTP Response (status code - 201 if successful, 409 if application already exists, 500 if onboard fails, 
        400 if namespace is not found, 403 if user is not part of namespace group)
        user: User object (validated by decorator ValidateAndReturnUser, expected role - Contributor)
    Returns:
        ApplicationResponse: Application object created, if successful
    """
    log.debug(
        f"Received POST request for create_Application with payload: \
        {json.dumps(application_request.json())}"
    )
    log.info(f"Checking if application with Name {application_request.name} already exists")

    app = await Application.find_one(Application.name == str(application_request.name),
                                     Application.onboard_status != OnboardStatus.FAILURE)

    if app:
        log.debug(f"application with Name {application_request.name} already exists, returning 409")
        response.status_code = status.HTTP_409_CONFLICT
        return app
    ns = await Namespace.find_one(Namespace.name == application_request.namespace)
    if ns is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=" Namesapce {} is not found while onboarding application {}".format(
                                application_request.namespace,
                                application_request.name))
    log.info(f"Creating application Object with Name {application_request.name} in DB")

    if await is_part_of_namespace_group(user, application_request.namespace):
        app = Application(id=str(uuid4()), **application_request.dict())
        app = init_common_model_attributes(app, user)
        app.onboard_status = await ApplicationOnboarder(app, user).onboard()
        await app.save()
        if app.onboard_status == OnboardStatus.FAILURE:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return app

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="User {} not allowed to bind application to namespace {} ".format(user.name,
                                                                                                 application_request.namespace))


@router.get(
    "",
    response_model=ApplicationListResponse,
    response_model_by_alias=False,
    summary=GET_ALL_APPLICATIONS_ROUTE_SUMMARY,
    response_model_exclude_none=True,
)
async def get_applications(query: str = None, user: User = Depends(
    ValidateAndReturnUser(expected_roles=[settings.READER_ROLE_NAME]))) -> ApplicationListResponse:
    """
    Returns all applications
    Args:
        query: Query string to filter applications
        user: User object (validated by decorator ValidateAndReturnUser, reader role is checked in decorator)  
    Returns:
        ApplicationListResponse: List of applications
    """
    log.debug(
        f"Received GET request for all Applications  \
              with query params: ${query} "
    )

    apps = await fetch_applications(query=query, user=user)

    return ApplicationListResponse(
        items=await filter_apps_not_authorized(user, apps),
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_APPLICATION_BY_ID_ROUTE_SUMMARY,
)
async def get_application_by_id(application_id: str, user: User = Depends(ValidateAndReturnUser(expected_roles=[
    settings.READER_ROLE_NAME]))) -> ApplicationResponse:
    """
    Returns application by Id
    Args:
        application_id: Id of the application
        user: User object (validated by decorator ValidateAndReturnUser, reader role is checked in decorator)
    Returns:
        ApplicationResponse: Application object
        HTTPException: 404 if application not found
    """
    log.debug(f"Received GET Request for application By Id : {application_id}")
    app = await Application.get(application_id)
    if app is not None:
        if await is_part_of_namespace_group(user, app.namespace):
            return app
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User is not authorized to access application with application with ID: {application_id}"
            )
    else:
        log.warning(f"application_id: {application_id} not Found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"application with {application_id} \
            not found.",
        )
