import time
from typing import List, Optional
from uuid import uuid4

from beanie import Document
from pydantic import Field

from app.core.schemas.applications import ApplicationResponse
from app.core.schemas.clusters import ClusterResponse


class ClusterState(Document):
    id: Optional[str] = Field(
        None, description="The unique identifier of the Deployment", alias="_id"
    )
    cluster: ClusterResponse = Field(ClusterResponse, description="Cluster details")
    applications: List[ApplicationResponse] = Field(ApplicationResponse, description="List of Application objects")
    createdOn: Optional[float] = Field(time.time(), description="created date epoch")
    ModifiedOn: Optional[float] = Field(time.time(), description="created date epoch")

    @staticmethod
    async def upsert_cluster_state(cluster_id: str, cluster: ClusterResponse, applications: List[ApplicationResponse]):
        cluster_state_obj = await ClusterState.find_one(ClusterState.cluster._id == cluster_id)
        if not cluster_state_obj:
            cluster_state_obj = ClusterState(
                id=str(uuid4()), cluster=cluster)
        cluster_state_obj.applications = applications if applications is not None else cluster_state_obj.applications
        cluster_state_obj.cluster = cluster if cluster is not None else cluster_state_obj.cluster
        return await cluster_state_obj.save()
