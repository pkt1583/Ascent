import logging
from logging import getLogger

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from app.api.api import api_router
from app.core.config import get_settings
from app.core.models.models import init_odm, init_env_cache
from app.utils.exceptions import add_exception_handler
from app.utils.instrumentation_utils import configure_instrumentation, TraceIdInjectionMiddleware

settings = get_settings()

logging.basicConfig(level=settings.CONSOLE_LOG_LEVEL)
# This always must be before fastapi.FastAPI and after logging.basicConfig
configure_instrumentation()

# Must use fastapi.FastAPI and not direct from fastapi import FastAPI. Opentelemetry limitation
app = fastapi.FastAPI(
    description=settings.API_DESCRIPTON,
    version=settings.VERSION,
    title=settings.API_TITLE,
    openapi_url=f"{settings.VERSION}/openapi.json",
    middleware=[Middleware(TraceIdInjectionMiddleware)]
)

add_exception_handler(app=app)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    log = getLogger(__name__)
    log.info("Starting the Application Up.")
    log.info("Establishing connection with Cosmos DB.")
    await init_odm(settings=settings)
    log.info("Populating environment cache")
    await init_env_cache()


app.include_router(api_router, prefix=settings.VERSION)
