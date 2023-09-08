import time
from typing import Dict, Optional

from beanie import Document
from pydantic import Field

from app.utils.enums import OnboardStatus, Operation


class TargetPolicy(Document):

    id: str = Field(
        None,
        description="The unique identifier for the \
        TargetPolicy",
        alias="_id",
    )
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
    created_on: Optional[float] = Field(time.time(), description="created date epoch")
    updated_on: Optional[float] = Field(time.time(), description="updated date epoch")

    app_selector: Optional[Dict[str, str]] = Field(
        None, description="The app Selector labels for the TargetPolicy"
    )
    cluster_selector: Optional[Dict[str, str]] = Field(
        None, description="The cluster Selector labels for the TargetPolicy"
    )
    onboard_status: OnboardStatus = Field(None, description="Onboarding status of application")
    operation: Operation = Field(None, description="Target policy operation. It could be either create "
                                                                "or purge")

    def __hash__(self):
        return hash((
            self.name
        ))
