from logging import getLogger
from uuid import uuid4

from fastapi import APIRouter, Request, Response, status, Depends, HTTPException, Query

from app.api.endpoints import ValidateAndReturnUser
from app.core.auth.user import User
from app.core.config import get_settings
from app.core.models.targetpolicies import TargetPolicy
from app.core.schemas.targetpolicies import (
    TargetPolicyListResponse,
    TargetPolicyRequest,
    TargetPolicyResponse,
)
from app.core.services import targetpolicies
from app.core.services.onboarder import TargetPolicyOnboarder
from app.core.services.targetpolicies import is_authorized_to_target
from app.utils.common import init_common_model_attributes
from app.utils.constants import (
    CREATE_TARGETPOLICY_ROUTE_SUMMARY,
    GET_ALL_TARGETPOLICY_ROUTE_SUMMARY,
    GET_TARGETPOLICY_BY_APP_NAME_ROUTE_SUMMARY)
from app.utils.enums import OnboardStatus

router = APIRouter()

log = getLogger(__name__)

settings = get_settings()


@router.post(
    "",
    response_model=TargetPolicyResponse,
    response_model_by_alias=False,
    status_code=201,
    response_model_exclude_none=True,
    summary=CREATE_TARGETPOLICY_ROUTE_SUMMARY,
)
async def create_target_policy(
        target_policy_request: TargetPolicyRequest, request: Request, response: Response,
        user: User = Depends(ValidateAndReturnUser(
            expected_roles=[settings.CONTRIBUTOR_ROLE_NAME]))
) -> TargetPolicyResponse:
    """
    Creates a new TargetPolicy
    Args:
        target_policy_request: TargetPolicy object to be created
        request: Request
        response: HTTP Response (status code - 201 if successful, 409 if TargetPolicy already exists, 500 if onboard fails)
        user: User (expected role - contributor)
    Returns:
        TargetPolicyResponse: TargetPolicy object created, if successful
    Exceptions:
        HTTPException: 403 if user is not allowed to target apps with given selector on cluster with given selector, 500 internal server error
    """
   
    log.info(
        f"Received request to {target_policy_request.operation} TargetPolicy with name {target_policy_request.name}"
    )

    log.debug(f"Persisting TargetPolicy {target_policy_request.name} to DB")

    target_policy = TargetPolicy(id=str(uuid4()), **target_policy_request.dict())

    """
    If the user is authorized to target the apps with the given selector on the cluster with the given selector,
    """
    if await is_authorized_to_target(user, target_policy_request.app_selector, target_policy_request.cluster_selector):
        target_policy.onboard_status = await TargetPolicyOnboarder(target_policy, user).onboard()
        target_policy = init_common_model_attributes(target_policy, user)
        await target_policy.save()
        if target_policy.onboard_status == OnboardStatus.FAILURE:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return target_policy

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="User {} not allowed to target apps with selector {} on cluster with selector {} ".format(
                            user.name,
                            target_policy_request.app_selector,
                            target_policy_request.cluster_selector))


@router.get(
    "",
    response_model=TargetPolicyListResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_ALL_TARGETPOLICY_ROUTE_SUMMARY,
)
async def get_target_policies(query: str = None, user: User = Depends(ValidateAndReturnUser(
    expected_roles=[settings.CONTRIBUTOR_ROLE_NAME]))) -> TargetPolicyListResponse:
    """Get TargetPolicies Based on query
    Args:
        query (str, optional): Query to filter TargetPolicies. Defaults to None.
        user (User, optional): user (expected role - contributor)
    Returns:
        TargetPolicyListResponse: List of TargetPolicies        
    """
    log.debug("Received GET request for all TargetPolicies")
    target_policies = await targetpolicies.fetch_target_policies(query=query)

    return TargetPolicyListResponse(
        items=target_policies,
    )

@router.get(
    "/{app_name}",
    response_model=TargetPolicyListResponse,
    response_model_by_alias=False,
    response_model_exclude_none=True,
    summary=GET_TARGETPOLICY_BY_APP_NAME_ROUTE_SUMMARY,
)
async def get_effective_target_policies_of_app(app_name: str = None, cluster_name: str = Query(None), user: User = Depends(ValidateAndReturnUser(
    expected_roles=[settings.READER_ROLE_NAME]))) -> TargetPolicyListResponse:
    """Get TargetPolicies based on app_name and cluster_name
    Args:
        app_name  (str): Name of application
        cluster_name  (str, optional): Query to filter TargetPolicies based on cluster name
        user (User, optional): user (expected role - Reader)
    Returns:
        TargetPolicyListResponse: List of TargetPolicies        
    """
    log.debug("Received GET request for effective TargetPolicies of application")
    # Get all target policies with matching the app_name and cluster selectors
    target_policies = await targetpolicies.get_effective_target_policies_for_application_on_cluster(user, app_name, cluster_name)
    
    # Return the first target policy when the list is non-empty, else return an empty list
    return TargetPolicyListResponse(items=[target_policies[0]] if target_policies else [])
