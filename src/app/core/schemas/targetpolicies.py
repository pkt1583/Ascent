from typing import Dict, List, Optional

from pydantic import BaseModel, Extra, Field, validator, root_validator

from app.utils.common import validate_name
from app.utils.enums import OnboardStatus, Operation


class TargetPolicyRequest(BaseModel):
    name: str = Field(description="The name of the TargetPolicy")
    description: Optional[str] = Field(
        None, description="A description of the TargetPolicy"
    )
    app_selector: Dict[str, str] = Field(
        description="The app Selector labels for the TargetPolicy"
    )
    cluster_selector: Dict[str, str] = Field(
        description="The cluster Selector labels for the TargetPolicy"
    )
    operation: Operation = Field(Operation.CREATE,
                                 description="Target policy operation. It could be either create or purge")

    @validator("name")
    def validate_name(cls, name):
        return validate_name(name)

    @root_validator(pre=True)
    def validate_only_name_allowed_for_purge(cls, values):
        app_selectors = values.get('app_selector')
        if len(app_selectors) == 0:
            raise ValueError("Atleast one value in  app selector is mandatory")
        cluster_selector = values.get("cluster_selector")
        if len(cluster_selector) == 0:
            raise ValueError("Atleast one value in cluster selector is mandatory")
        operation = values.get('operation')
        if operation == Operation.PURGE:
            app_selector: dict[str, str] = values.get("app_selector")
            if set(app_selector.keys()) != {'name'}:
                raise ValueError("Invalid app selector. Only 'name' key is allowed for purge")
        return values


    class Config:
        allow_population_by_field_name = True


class TargetPolicyResponse(BaseModel):
    id: str = Field(None, description="The id of the TargetPolicy", alias="_id")
    name: Optional[str] = Field(None, description="The name of the TargetPolicy")
    description: Optional[str] = Field(
        None, description="A description of the TargetPolicy"
    )
    created_by: Optional[str] = Field(
        None, description="details of user who created the TargetPolicy"
    )
    updated_by: Optional[str] = Field(
        None, description="details of user who updated the TargetPolicy"
    )
    created_on: Optional[float] = Field(None, description="created date epoch")
    updated_on: Optional[float] = Field(None, description="updated date epoch")
    app_selector: Optional[Dict[str, str]] = Field(
        None, description="The app Selector labels for the TargetPolicy"
    )
    cluster_selector: Optional[Dict[str, str]] = Field(
        None, description="The cluster Selector labels for the TargetPolicy"
    )
    onboard_status: OnboardStatus = Field(None, description="Onboarding status of target policy")
    operation: Operation = Field(None,
                                 description="Target policy operation. It could be either create or purge")

    class Config:
        allow_population_by_field_name = True


class TargetPolicyListResponse(BaseModel):
    class Config:
        extra = Extra.forbid

    items: Optional[List[TargetPolicyResponse]] = Field(
        None, description="The list of DataStreams"
    )
