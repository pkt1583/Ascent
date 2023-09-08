from logging import getLogger

from app.core.auth.user import User
from app.core.models.targetpolicies import TargetPolicy
from app.core.services.clusters import fetch_clusters, is_allowed_on_cluster
from app.core.services.applications import get_apps_by_selector
from app.utils.common import create_filter_condition
from app.utils.common import dict_to_query_string
from app.utils.enums import EventType, Operation

log = getLogger(__name__)


async def fetch_affected_target_policies(metadata, eventype):
    actualTargetPolicies = []
    matched = []

    log.info(
        f"Fetching affected target_policies for metadata: {metadata} and eventype: {eventype}"
    )
    # We will iterate through "each" metadata(key:value) pair from the onboarded cluster "metadata" object or app "metadata" object
    for key, value in metadata.items():
        queryString = None

        # Get the query string for the current metadata key:value pair, for example, if the metadata is {"edge": "true"},
        # then the query string will be "app_selector.edge=true" if the eventype is APPLICATION_ONBOARDING or
        # "cluster_selector.edge=true" if the eventype is CLUSTER_ONBOARDING
        # parentKey is used to specify the parent key of the metadata inside which we have to look for  , that is app_selector in the case of APPLICATION_ONBOARDING
        # and cluster_selector in the case of CLUSTER_ONBOARDING
        if EventType.CLUSTER_ONBOARDING == eventype:
            queryString = dict_to_query_string({key: value}, parent_key="cluster_selector")
        elif EventType.APP_ONBOARDING == eventype:
            queryString = dict_to_query_string({key: value}, parent_key="app_selector")

        # Fetch all the target_policies that match the individual metadata for example, if the metadata is {"edge": "true"},
        # then we will fetch all the target_policies that have app_selector.edge = true if the eventype is APPLICATION_ONBOARDING
        # or cluster_selector.edge = true if the eventype is CLUSTER_ONBOARDING
        target_policies = await fetch_target_policies(queryString)

        # We will then for each matching target policy, find all the apps or clusters that match the app_selector or cluster_selector property
        # It should be noted that the app_selector and cluster_selector are AND conditions, so if the app_selector is {"edge": "true", "region": "us-east-1"}
        # then we will fetch all the apps that have edge = true AND region = us-east-1
        # All the current_target_policy labels should match completely with the metadata of the newly onboarded cluster or app
        for target_policy in target_policies:
            if EventType.CLUSTER_ONBOARDING == eventype:
                # We are checking if the current current_target_policy cluster_selector completely matches the metadata of the newly onboarded cluster
                matched = await compare_metadata(
                    target_policy.cluster_selector, metadata
                )
            else:
                matched = await compare_metadata(target_policy.app_selector, metadata)

            # If the target Policy matches the metadata of the newly onboarded cluster or app,
            # that means that this current_target_policy has to be deployed on the newly onboarded cluster or app
            if matched:
                actualTargetPolicies.append(target_policy)
    actualTargetPolicies.sort(key=lambda p: p.updated_on)
    return actualTargetPolicies


async def fetch_target_policies(query: str = None):
    """A helper function to fetch TargetPolicies from the database based on the query

    Args:
        query (str, optional): Query string to filter the TargetPolicies. Defaults to None.

    Returns:
        _type_: The list of TargetPolicies that match the query
    """
    log.info(f"Fetching TargetPolicies with query: {query}")
    target_policies = await TargetPolicy.find(
        create_filter_condition(query_params=query)
    ).to_list()
    log.info(
        f"Found {len(target_policies)} TargetPolicies, values: {target_policies} with query: {query}"
    )
    return target_policies


async def compare_metadata(target_policySelector, metadata):
    """A helper function to check if the metadata of the newly onboarded cluster or app matches the target_policySelector app_selector or cluster_selector

    Args:
        target_policySelector Dict: The app_selector or cluster_selector of the current_target_policy
        metadata Dict : Metadata of the newly onboarded cluster or app

    Returns:
        Boolean : True if the metadata matches the target_policySelector, False otherwise
    """
    for key, value in target_policySelector.items():
        if key not in metadata or metadata[key] != value:
            log.info(
                f"The selector does not match the metadata for {metadata} with key: {key} and value: {value} "
            )
            return False
    log.info(
        f"The cluster_selector {target_policySelector} matches the cluster metadata {metadata}"
    )
    return True


async def is_authorized_to_target(user: User, app_selector: dict[str, str], cluster_selector: dict[str, str]):
    matched_clusters = await fetch_clusters(dict_to_query_string(
        cluster_selector, parent_key="metadata"
    ))

    if not await is_allowed_on_cluster(user, matched_clusters):
        log.warning("User tried targeting for clusters {} that is not authorized".format(
            matched_clusters))
        return False

    return True

async def get_effective_target_policies_for_application_on_cluster(user: User,app_name, cluster_name):
    try:
        log.info(
        f"Fetching effected target_policies for application: {app_name} and Cluster: {cluster_name}"
    )
        # Fetch the cluster metadata
        matched_clusters = await fetch_clusters(dict_to_query_string({"name": cluster_name}, parent_key="metadata"))
        if not matched_clusters:
            return []  # No clusters found, return empty list

        if not await is_allowed_on_cluster(user, matched_clusters):
            log.warning("User tried to get targets for clusters {} that is not authorized".format(
                matched_clusters))
            return []
        
        
        # Fetch the application metadata
        app = await get_apps_by_selector({"name": app_name}, user)
        app_metadata = app[0].metadata if app and app[0] else None

        effective_target_policies = set()  # Use a set to avoid duplicates

        for key, value in matched_clusters[0].metadata.items():
            cluster_selector = dict_to_query_string({key: value}, parent_key="cluster_selector")
            target_policies = await fetch_target_policies(cluster_selector)

            matched_policies = [target_policy for target_policy in target_policies
                                if await compare_metadata(target_policy.app_selector, app_metadata)]
            effective_target_policies.update(matched_policies)  # Add unique matched policies to the set

        effective_target_policies = sorted(effective_target_policies, reverse=True, key=lambda p: p.updated_on)
        return effective_target_policies
        
    except Exception as e:
        log.info(f"An error occurred in get_effective_target_policies_for_application_on_cluster due to: {e}")
        return []


class TargetPolicyWithMetadata:
    def __init__(self, target_policy_id: str, metadata: dict[str, str],
                 updated_on, operation: Operation = None):
        self.target_policy_id = target_policy_id
        self.metadata = metadata
        self.operation: Operation = operation
        self.updated_on = updated_on
    def __hash__(self):
        return hash((self.target_policy_id, tuple(sorted(self.metadata.items())), self.operation))

    def __eq__(self, other):
        if not isinstance(other, TargetPolicyWithMetadata):
            return False
        return (
                self.target_policy_id == other.target_policy_id
                and self.metadata == other.metadata
                and self.operation == other.operation
        )



