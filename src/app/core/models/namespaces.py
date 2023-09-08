import time
from typing import Optional, List

from beanie import Document, after_event, Insert, Replace
from pydantic import Field

from app.utils.common import popualate_env_cache


class Namespace(Document):
    id: Optional[str] = Field(
        None, description="The unique identifier for the namespace",alias="_id"
    )
    name: Optional[str] = Field(None, description="The name of the namespace")
    description: Optional[str] = Field(
        None, description="A description of the namespace"
    )
    cost_center: Optional[str] = Field(None, description="cost centers")
    group: List[str] = Field(
        None,
        description="Group name of the team owning this namespace. The contributors need to be "
                    "added to group name-contributors and readers to be added to group name-reader"
    )
    created_by: Optional[str] = Field(
        None, description="details of user who created the namespace"
    )
    updated_by: Optional[str] = Field(
        None, description="details of user who updated the namespace"
    )
    created_on: Optional[float] = Field(time.time(), description="created date epoch")
    updated_on: Optional[float] = Field(time.time(), description="updated date epoch")

    @after_event(Insert, Replace)
    async def populate_env_cache(self):
        await popualate_env_cache([group.split("-")[-1] for group in self.group])
