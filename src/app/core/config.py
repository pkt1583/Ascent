from functools import lru_cache
from os import environ
from typing import Optional

from pydantic import BaseSettings


class settings(BaseSettings):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    API_DESCRIPTON = "API for Control Plane Operations"
    API_TITLE = "Control Plane API "
    VERSION = "/v1"
    AZURE_COSMOS_CONNECTION_STRING: str = ""
    AZURE_COSMOS_DATABASE_NAME: str = ""
    APPLICATIONINSIGHTS_CONNECTION_STRING: Optional[str] = None
    ARGOCD_MASTER_APPLICATION_REPO_URL: str = "https://dev.azure.com/colesgroup/Intelligent%20Edge/_git/plat_manifests"
    OTEL_SERVICE_NAME: str = "Control Plane API"  # https://github.com/microsoft/ApplicationInsights-Python/tree/main/azure-monitor-opentelemetry
    CONSOLE_LOG_LEVEL: str = "INFO"  # has to be caps
    OTEL_PYTHON_LOG_LEVEL: str = "INFO"  # https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/logging/logging.html
    DISABLE_LOG_INSTRUMENTATION: bool = "False"
    DISABLE_TRACING_INSTRUMENTATION: bool = "False"
    DISABLE_METRICS_INSTRUMENTATION: bool = "True"
    OTEL_PYTHON_FASTAPI_EXCLUDED_URLS = "health,docs"  # https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
    AZURE_TENANT_ID: Optional[str] = None
    WEBSITE_AUTH_ENABLED: bool = False  # https://learn.microsoft.com/en-us/azure/app-service/reference-app-settings?tabs=kudu%2Cpython#authentication--authorization
    AZURE_CLIENT_ID: Optional[str] = None
    ADMIN_ROLE_NAME: Optional[str] = "admin"
    CONTRIBUTOR_ROLE_NAME: Optional[str] = "contributor"
    READER_ROLE_NAME: Optional[str] = "reader"
    CP_APP_NAME = "plat"
    VALID_ROLES: str = f"{ADMIN_ROLE_NAME},{CONTRIBUTOR_ROLE_NAME},{READER_ROLE_NAME}"
    BYPASS_AUTH_FOR_BEHAVE_TESTING = False
    IS_ON_APP_SERVICE = "WEBSITE_SITE_NAME" in environ
    FEATURE_RBAC_ENABLED = False  # TODO: Remove this after the groups are created.
    CP_AUTH_BYPASS_ENV = "nonprod"
    GROUP_NAME_SEPARATOR = "-"
    GROUP_PATTERN = r"([a-zA-Z0-9_-]+)" + GROUP_NAME_SEPARATOR + "([a-zA-Z]+)" + GROUP_NAME_SEPARATOR + "([a-zA-Z]+)"
    ADMIN_GROUP_PATTERN = r"" + CP_APP_NAME + "-[a-zA-Z]+" + GROUP_NAME_SEPARATOR + "" + ADMIN_ROLE_NAME
    GROUP_NODE_IN_DECODED_TOKEN = 'groups'
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return settings()
