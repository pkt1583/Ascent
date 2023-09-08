from logging import getLogger

from beanie.odm.operators.find.comparison import NE

from app.core.auth.user import User
from app.core.models.clusters import Cluster
from app.utils.common import create_filter_condition, dict_to_query_string
from app.utils.enums import OnboardStatus

log = getLogger(__name__)


async def fetch_clusters(query, find_operator=None, filter_failed=True):
    onboard_status_filer = {}
    if filter_failed:
        onboard_status_filer = NE(Cluster.onboard_status, OnboardStatus.FAILURE)
    if find_operator is None:
        find_operator = {}
    log.info(f"Fetching Clusters with query: {query}")
    clusters = await Cluster.find(create_filter_condition(query_params=query), find_operator,
                                  onboard_status_filer).to_list()
    log.info(f"Found {len(clusters)} Clusters, values: {clusters}")
    return clusters


async def is_allowed_on_cluster(user: User, clusters: list[Cluster]):
    allowed_envs = await user.role_collection.get_environments()
    envs_in_cluster = {cluster.environment for cluster in clusters}
    return allowed_envs >= envs_in_cluster


async def get_clusters_by_selector(cluster_selector):
    clusters_query_string = dict_to_query_string(
        cluster_selector, parent_key="metadata"
    )
    matched_clusters = await fetch_clusters(clusters_query_string)
    return matched_clusters
