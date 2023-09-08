from typing import List
from pydantic import BaseModel
from app.core.schemas.applications import ApplicationResponse
from app.core.schemas.clusters import ClusterResponse


class DeploymentState(BaseModel):
    add: List[ApplicationResponse]
    purge: List[ApplicationResponse]
    cluster_context : ClusterResponse

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
