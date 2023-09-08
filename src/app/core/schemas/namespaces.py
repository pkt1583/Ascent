import re
from typing import List, Optional

from pydantic import BaseModel, Extra, Field, validator, root_validator

from app.utils.common import validate_name


class NamespaceRequest(BaseModel):
    name: str = Field(..., description="The name of the Namespace")
    description: Optional[str] = Field(
        None, description="A description of the Namespace"
    )
    cost_center: Optional[str] = Field(None, description="cost centers")
    group: List[str] = Field(
        ..., description="Groups Id of the teams owning this namespace"
    )

    class Config:
        allow_population_by_field_name = True

    @validator("name")
    def validate_name(cls, name):
        return validate_name(name)

    @root_validator
    def validate_group(cls, values):
        groups = values.get("group")
        if len(groups) == 0:
            raise ValueError("group cannot be empty")
        pattern = r'-[a-zA-Z0-9]+$'
        for group in groups:
            if not re.search(pattern, group):
                raise ValueError(f"Invalid group name {group}. They must end with -env where env is environment name")
        return values

class NamespaceResponse(BaseModel):
    id: str = Field(
        None, description="The unique identifier for the Namespace", alias="_id"
    )
    name: str = Field(None, description="The name of the Namespace")
    description: Optional[str] = Field(
        None, description="A description of the Namespace"
    )
    cost_center: Optional[str] = Field(None, description="cost centers")
    group: List[str] = Field(
        None, description="Groups of the teams owning this namespace"
    )
    created_by: Optional[str] = Field(
        None, description="details of user who created the Namespace"
    )
    updated_by: Optional[str] = Field(
        None, description="details of user who updated the Namespace"
    )
    created_on: Optional[float] = Field(None, description="created date epoch")
    updated_on: Optional[float] = Field(None, description="updated date epoch")

    class Config:
        allow_population_by_field_name = True


class NamespaceListResponse(BaseModel):
    class Config:
        extra = Extra.forbid

    items: Optional[List[NamespaceResponse]] = Field(
        None, description="The list of Namespaces"
    )
