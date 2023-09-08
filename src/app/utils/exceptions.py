from logging import getLogger

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.schemas.error import ProblemDetails, ErrorDetail

log = getLogger(__name__)


def add_exception_handler(app):
    @app.exception_handler(StarletteHTTPException)
    async def HTTPExceptionHandler(request, exc):
        return JSONResponse(
            get_http_exception_payload(str(exc.detail), exc.status_code),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validationExceptionHandler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=get_request_validation_payload(exc=exc),
        )

    @app.exception_handler(Exception)
    async def exceptionHandler(request, err):
        return await populate_exception_details(request=request, err=err)


async def populate_exception_details(request, err) -> JSONResponse:
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    error_details = {"message": f"{base_error_message}. Detail: {err}"}
    log.info(error_details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=get_un_catched_exception_payload(error_details),
    )
def get_request_validation_payload(exc):
    """_summary_

    Args:
        exc (_type_): _description_

    Returns:
        _type_: _description_
    """
    error_details = []
    property_name = ""
    property_error = ""
    for error in exc.errors():
        if "loc" in error and len(error["loc"]) >= 1:
            property_name = error["loc"][1]
        if "msg" in error:
            property_error = f"{error['msg']} : {error['type']} "
        error_detail = ErrorDetail(
            propertyName=property_name, propertyError=property_error
        )
        error_details.append(error_detail)

    problem_details_obj = ProblemDetails(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        description="Request Validation Exception Occcured",
        details=error_details,
    )

    return jsonable_encoder(problem_details_obj)


def get_http_exception_payload(error_message, status_code):

    problem_details_obj = ProblemDetails(code=status_code, description=error_message)
    return jsonable_encoder(problem_details_obj)


def get_un_catched_exception_payload(error_message):

    problem_details_obj = ProblemDetails(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR, description=str(error_message)
    )

    return jsonable_encoder(problem_details_obj)
