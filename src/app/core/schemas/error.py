from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ErrorDetail(BaseModel):
    propertyName: Optional[str] = Field(
        None, description="name of the field in the request which has the error"
    )
    propertyError: Optional[str] = Field(
        None, description="the error associated with the property"
    )


class ProblemDetails(BaseModel):
    code: Optional[str] = Field(
        None,
        description="An application-specific error code, expressed as a string value.",
    )
    description: Optional[str] = Field(
        None,
        description="A human-readable explanation specific to this occurrence of the problem. Like title, this field's value can be localized.",
    )
    details: Optional[List[ErrorDetail]] = None

