import time
from typing import Dict, Optional
from beanie import Document
from pydantic import Field
from app.core.schemas.deployment import DeploymentState
from app.utils.enums import DeploymentStatus


class Deployment(Document):
    id: Optional[str] = Field(
        None, description="The unique identifier of the Deployment", alias="_id"
    )

    deployment_mappings: Dict[str, DeploymentState] = Field(
        None, description="deployment mappings"
    )
    created_on: Optional[float] = Field(time.time(), description="created date epoch")
    target_policy_id: str = Field(None, description="target policy id")
    status: Optional[DeploymentStatus] = Field(None, description="deployment status")
