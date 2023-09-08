from logging import getLogger
from typing import List

from app.core.auth.user import User
from app.core.models.applications import Application
from app.core.services.namespaces import get_authorized_namespace_by_names
from app.utils.common import create_filter_condition, dict_to_query_string
from app.utils.enums import OnboardStatus

log = getLogger(__name__)


# TODO: Never return unauthorized apps. Is there way to add this everywhere
async def fetch_applications(query, user, filter_failed=True):
    """Fetch Applications from the database based on the query"""
    log.info(f"Fetching Applications with query: {query}")

    if filter_failed:
        app = await Application.find(
            create_filter_condition(query_params=query), Application.onboard_status != OnboardStatus.FAILURE
        ).to_list()
    else:
        app = await Application.find(
            create_filter_condition(query_params=query)
        ).to_list()

    log.info(f"Found {len(app)} Applications, value: {app}")
    return await filter_apps_not_authorized(user, app)


async def filter_apps_not_authorized(user, apps: List[Application]):
    authorized_namespaces = await get_authorized_namespace_by_names(user=user,
                                                                    namespace_names={application.namespace for
                                                                                     application in apps})
    authorized_namespaces_name = {ns.name for ns in authorized_namespaces}
    filtered_applications = [app for app in apps if app.namespace in authorized_namespaces_name]
    return filtered_applications


async def get_apps_by_selector(app_selector, user: User):
    apps_query_string = dict_to_query_string(app_selector, parent_key="metadata")
    matched_apps = await fetch_applications(query=apps_query_string, user=user)
    return matched_apps
