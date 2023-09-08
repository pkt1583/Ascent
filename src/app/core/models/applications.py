import time
from typing import Dict, Optional

from beanie import Document
from pydantic import Field

from app.utils.enums import OnboardStatus


class Application(Document):
    id: Optional[str] = Field(
        None, description="The unique identifier for the cluster", alias="_id"
    )
    name: str = Field(None, description="The name of the cluster")
    description: Optional[str] = Field(None, description="A description of the cluster")
    repo_url: str = Field(None, description="The repo_url of the application")
    repo_branch: Optional[str] = Field(
        "main", description="The repo_branch of the application"
    )
    repo_path: str = Field(None, description="The repo_path of the application")
    created_by: Optional[str] = Field(
        None, description="details of user who created the cluster"
    )
    updated_by: Optional[str] = Field(
        None, description="details of user who updated the cluster"
    )
    created_on: Optional[float] = Field(time.time(), description="created date epoch")
    updated_on: Optional[float] = Field(time.time(), description="updated date epoch")
    metadata: Optional[Dict[str, str]] = Field(
        None, description="The metadata for the cluster"
    )
    namespace: str = Field(None, description="The namespace for the application")
    onboard_status: OnboardStatus = Field(None, description="Onboarding status of application")

    def __hash__(self):
        # Include the relevant attributes in the hash calculation
        return hash(self.name)
