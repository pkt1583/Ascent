from fastapi import APIRouter
from app.api.endpoints import clusters, applications, namespaces, targetpolicies
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()

api_router.include_router(
    clusters.router,
    prefix="/clusters",
    tags=["Clusters"],
)

api_router.include_router(
    applications.router,
    prefix="/applications",
    tags=["Applications"],
)

api_router.include_router(
    namespaces.router,
    prefix="/namespaces",
    tags=["Namespaces"],
)

api_router.include_router(
    targetpolicies.router,
    prefix="/targetpolicies",
    tags=["TargetPolicies"],
)