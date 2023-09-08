from typing import Dict, List, Optional

from pydantic import BaseModel, Extra, Field, validator, root_validator

from app.utils.common import validate_name
from app.utils.enums import OnboardStatus


class ClusterRequest(BaseModel):
    name: str = Field(..., description="The name of the cluster")
    description: Optional[str] = Field(None, description="A description of the cluster")
    short_name: Optional[str] = Field(None, description="A short name of the cluster")
    environment: str = Field(..., description="Name of environment")
    metadata: Optional[Dict[str, str]] = Field(
        None, description="The metadata for the cluster"
    )

    class Config:
        allow_population_by_field_name = True

    @validator("name")
    def validate_name(cls, name):
        return validate_name(name)

    @validator("environment")
    def validate_environment(cls, environment):
        return validate_name(environment)

    @root_validator(pre=True)
    def validate_name_and_id_not_allowed_in_meta(cls, values):
        metadata = values.get('metadata')
        if metadata is not None and len(metadata) != 0:
            metadata_keys = set(metadata.keys())
            if 'name' in metadata_keys or 'id' in metadata_keys:
                raise ValueError("Name and Id are reserved attributes and cannot be supplied by request body")
        return values

class ClusterResponse(BaseModel):
    id: str = Field(
        None, description="The unique identifier for the cluster", alias="_id"
    )
    name: str = Field(None, description="The name of the cluster")
    description: Optional[str] = Field(None, description="A description of the cluster")
    short_name: Optional[str] = Field(None, description="A short name of the cluster")
    environment: str = Field(None, description="Name of environment")
    metadata: Optional[Dict[str, str]] = Field(
        None, description="The metadata for the cluster"
    )
    created_by: Optional[str] = Field(
        None, description="details of user who created the cluster"
    )
    updated_by: Optional[str] = Field(
        None, description="details of user who updated the cluster"
    )
    created_on: Optional[float] = Field(None, description="created date epoch")
    updated_on: Optional[float] = Field(None, description="updated date epoch")
    onboard_status: OnboardStatus = Field(None, description="Onboarding status of cluster")

    class Config:
        allow_population_by_field_name = True


class ClusterListResponse(BaseModel):
    class Config:
        extra = Extra.forbid

    items: Optional[List[ClusterResponse]] = Field(
        None, description="The list of Clusters"
    )
