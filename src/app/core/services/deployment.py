from abc import abstractmethod, ABC
from logging import getLogger
from typing import Dict
from uuid import uuid4

from app.core.auth.user import User
from app.core.models.applications import Application
from app.core.models.clusters import Cluster
from app.core.models.deployment import Deployment
from app.core.models.targetpolicies import TargetPolicy
from app.core.schemas.deployment import DeploymentState
from app.core.services.applications import get_apps_by_selector
from app.core.services.clusters import get_clusters_by_selector
from app.core.services.purge_policies import ApplyOnceCronologicalOrderedPurgePolicy
from app.utils.enums import DeploymentStatus, Operation

log = getLogger(__name__)


class DeploymentMappingCreator(ABC):
    """This creates the deployment state and populates it into deployment mappings"""

    async def create_deployment_mappings(self, matched_apps, matched_clusters):
        deployment_mapping: Dict[str, DeploymentState] = {
            cluster.id: DeploymentState(add=[], purge=[], cluster_context=cluster) for cluster in
            matched_clusters}
        self.populate_apps(deployment_mapping, matched_apps)
        return deployment_mapping

    @abstractmethod
    def populate_apps(self, deployment_mappings: Dict[str, DeploymentState], matched_apps):
        """Modifies the deployment mapping based on operation. Currently supported operations are purge and create. They will
        either add apps to purge array or add apps to add array"""
        raise NotImplemented("Need concrete class for implementation")


class CreateDeploymentMappingCreator(DeploymentMappingCreator):
    """This class is responsible to add applications to deployment_mapping add array"""

    def populate_apps(self, deployment_mappings: Dict[str, DeploymentState], matched_apps):
        for key, deployment_mapping in deployment_mappings.items():
            deployment_mapping.add += matched_apps


class PurgeDeploymentMappingCreator(DeploymentMappingCreator):
    """This class is responsible toadd applications to deployment_mapping purge array"""

    def populate_apps(self, deployment_mappings: Dict[str, DeploymentState], matched_apps):
        for key, deployment_mapping in deployment_mappings.items():
            deployment_mapping.purge += matched_apps


"""Deployment mapping registry holds mapping of operation and corresponding creator. These creators currently modify add/purge array"""
_deployment_mapping_registry = {Operation.CREATE: CreateDeploymentMappingCreator(),
                                Operation.PURGE: PurgeDeploymentMappingCreator()}


class DeploymentParameters:
    """Wrapper class for argument of create_deployment. This was created so that there is no linting issue with overriden methods.
    In certain cases the methods expect targetpolicy and cluster whereas in some other cases they need cluster only, so the arguments will change.
    **kwargs is not used because it does not give hints to caller on what parameters are"""

    def __init__(self, user: User, targetPolicy: TargetPolicy = None, cluster: Cluster = None, application: Application = None):
        self.user = user
        self.targetpolicy = targetPolicy
        self.cluster = cluster
        self.application = application


class DeploymentService(ABC):

    @abstractmethod
    async def create_deployment_object(self, parameters: DeploymentParameters):
        """Create deployment service object either on cluster or application or targetpolicy onboarding"""


async def split_policies(target_policies):
    purge_policies = {affected_target_policy for affected_target_policy in target_policies if
                      affected_target_policy.operation == Operation.PURGE}
    non_purge_policies = {affected_target_policy for affected_target_policy in target_policies if
                          affected_target_policy.operation != Operation.PURGE}
    return non_purge_policies, purge_policies


class ClusterOrApplicationDeploymentService(DeploymentService, ABC):
    def __init__(self, operation=Operation.CREATE):
        self.deployment_mapping_creator = _deployment_mapping_registry.get(Operation.CREATE)
        self.purge_policy_evaluator = ApplyOnceCronologicalOrderedPurgePolicy()

    async def create_deployment_object(self, parameters: DeploymentParameters):
        """Find matching metadata_based_resources
                2) Apply Purge policies and filter the matching metadata_based_resources
                3) Invoke deployment mapping creator to create deployment mappings
                4) Create deployment object and return back"""
        target_policies = parameters.targetpolicy
        log.info(
            f"Creating Deployment object for target_policies: {target_policies} "
        )
        non_purge_policies, purge_policies = await split_policies(target_policies)
        target_policy_ids = []
        master_deployment_mapping: Dict[str, DeploymentState] = {}
        already_evaluate_purged_policies = []  # so that it gets matched only once for each create
        for target_policy in non_purge_policies:
            log.info(f"Creating Deployment object for target_policy: {target_policy}")
            deployment_mapping = await self._create_deployment_mapping(already_evaluate_purged_policies, parameters,
                                                                       purge_policies, target_policy)
            target_policy_ids.append(target_policy.id)
            for cluster_id, deployment_state in deployment_mapping.items():
                deploy_state: DeploymentState = master_deployment_mapping.get(cluster_id)
                if deploy_state is None:
                    master_deployment_mapping[cluster_id] = deployment_state
                else:
                    deploy_state.add.extend(deployment_state.add)
        if len(non_purge_policies) != 0:
            return await Deployment(id=str(uuid4()), target_policy_id=",".join(target_policy_ids),
                                    deployment_mappings=master_deployment_mapping,
                                    status=DeploymentStatus.PENDING).save()  # type: ignore

    @abstractmethod
    async def _create_deployment_mapping(self, already_evaluate_purged_policies, parameters, purge_policies,
                                         target_policy):
        raise NotImplemented("Need concrete class for implementation of create_deployment_mapping")


class ClusterDeploymentService(ClusterOrApplicationDeploymentService):

    def __init__(self, operation=Operation.CREATE):
        self.deployment_mapping_creator = _deployment_mapping_registry.get(operation)
        self.purge_policy_evaluator = ApplyOnceCronologicalOrderedPurgePolicy()

    async def _create_deployment_mapping(self, already_evaluate_purged_policies, parameters, purge_policies,
                                         current_target_policy):
        log.info(f"Creating Deployment object for target_policy: {current_target_policy}")
        matched_apps: list[Application] = self.purge_policy_evaluator.filter_purged(
            metadata_based_resources=await get_apps_by_selector(current_target_policy.app_selector,
                                                                user=parameters.user),
            purge_policies=purge_policies,
            policy_under_evaluation=current_target_policy,
            already_evaluate_purged_policies=already_evaluate_purged_policies,
        )
        log.debug(
            f"Matched Apps: {matched_apps} for target_policy: {current_target_policy} and cluster: {parameters.cluster}")
        deployment_mapping = await self.deployment_mapping_creator.create_deployment_mappings(matched_apps,
                                                                                              [parameters.cluster])
        return deployment_mapping


class AppDeploymentService(ClusterOrApplicationDeploymentService):
    def __init__(self, operation=Operation.CREATE):
        self.deployment_mapping_creator = _deployment_mapping_registry.get(operation)
        self.purge_policy_evaluator = ApplyOnceCronologicalOrderedPurgePolicy()

    async def _create_deployment_mapping(self, already_evaluate_purged_policies, parameters, purge_policies,
                                         current_target_policy):
        matched_clusters = self.purge_policy_evaluator.filter_purged(
            metadata_based_resources=await get_clusters_by_selector(current_target_policy.cluster_selector),
            user=parameters.user, purge_policies=purge_policies,
            policy_under_evaluation=current_target_policy,
            already_evaluate_purged_policies=already_evaluate_purged_policies)
        log.info(
            f"Matched Clusters: {matched_clusters} for app: {parameters.application} and target_policy: {current_target_policy}")

        deployment_mapping = await self.deployment_mapping_creator.create_deployment_mappings([parameters.application],
                                                                                              matched_clusters)
        return deployment_mapping


class TargetPolicyDeploymentService(DeploymentService):
    def __init__(self, operation: Operation):
        self.deployment_mapping_creator = _deployment_mapping_registry.get(operation)

    async def create_deployment_object(self, parameters: DeploymentParameters):
        log.info(f"Creating Deployment object for target_policy: {parameters.targetpolicy}")
        matched_apps = await get_apps_by_selector(parameters.targetpolicy.app_selector, parameters.user)
        if len(matched_apps) == 0:
            return None
        matched_clusters = await get_clusters_by_selector(parameters.targetpolicy.cluster_selector)
        deployment_mapping = await self.deployment_mapping_creator.create_deployment_mappings(matched_apps,
                                                                                              matched_clusters)

        return await Deployment(id=str(uuid4()), target_policy_id=parameters.targetpolicy.id,
                                deployment_mappings=deployment_mapping,
                                status=DeploymentStatus.PENDING).save()  # type: ignore
