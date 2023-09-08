import time
from typing import Dict, Optional

from beanie import Document, after_event, Insert, Replace
from pydantic import Field

from app.utils.common import popualate_env_cache
from app.utils.enums import OnboardStatus


class Cluster(Document):
    id: Optional[str] = Field(None, description="The unique identifier for the cluster",alias="_id")
    name: Optional[str] = Field(None, description="The name of the cluster")
    description: Optional[str] = Field(None, description="A description of the cluster")
    short_name: Optional[str] = Field(None, description="A description of the cluster")
    environment: Optional[str] = Field(None, description="Name of the environment")
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
    onboard_status: OnboardStatus = Field(None, description="Onboarding status of cluster")

    @after_event(Insert, Replace)
    async def populate_env_cache(self):
        await popualate_env_cache([self.environment])
