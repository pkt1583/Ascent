from typing import Dict, List, Optional

from pydantic import BaseModel, Extra, Field, validator, root_validator

from app.utils.common import validate_name
from app.utils.enums import OnboardStatus


class ApplicationRequest(BaseModel):
    name: str = Field(..., description="The name of the application")
    description: Optional[str] = Field(
        None, description="A description of the application"
    )
    repo_url: str = Field(..., description="The repo_url of the application")
    repo_branch: Optional[str] = Field(
        'master', description="The repo_branch of the application"
    )
    repo_path: str = Field(..., description="The repo_path of the application")

    metadata: Optional[Dict[str, str]] = Field(
        None, description="The metadata for the cluster"
    )
    namespace: str = Field(..., description="The namespace for the application")

    class Config:
        allow_population_by_field_name = True

    @validator("name")
    def validate_name(cls, name):
        return validate_name(name)

    @root_validator(pre=True)
    def validate_name_and_id_not_allowed_in_meta(cls, values):
        metadata = values.get('metadata')
        if metadata is not None and len(metadata) != 0:
            metadata_keys = set(metadata.keys())
            if 'name' in metadata_keys or 'id' in metadata_keys:
                raise ValueError("Name and Id are reserved attributes and cannot be supplied by request body")
        return values

class ApplicationResponse(BaseModel):
    id: str = Field(
        None, description="The unique identifier for the cluster", alias="_id"
    )
    name: str = Field(None, description="The name of the cluster")
    description: Optional[str] = Field(None, description="A description of the cluster")
    created_by: Optional[str] = Field(
        None, description="details of user who created the cluster"
    )
    updated_by: Optional[str] = Field(
        None, description="details of user who updated the cluster"
    )
    created_on: Optional[int] = Field(None, description="created date epoch")
    updated_on: Optional[int] = Field(None, description="updated date epoch")

    repo_url: str = Field(None, description="The repo_url of the application")
    repo_branch: str = Field(
        None, description="The repo_branch of the application"
    )
    repo_path: str = Field(None, description="The repo_path of the application")
    namespace: str = Field(None, description="The namespace for the application")

    metadata: Optional[Dict[str, str]] = Field(
        None, description="The metadata for the application"
    )
    onboard_status: OnboardStatus = Field(None, description="Onboarding status of application")
    class Config:
        allow_population_by_field_name = True


class ApplicationListResponse(BaseModel):
    class Config:
        extra = Extra.forbid

    items: Optional[List[ApplicationResponse]] = Field(
        None, description="The list of Applications"
    )
