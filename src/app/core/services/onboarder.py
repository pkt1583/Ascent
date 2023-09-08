from abc import ABC, abstractmethod
from logging import getLogger

from app.core.config import get_settings
from app.core.models.clusters import Cluster
from app.core.models.clusterstate import ClusterState
from app.core.models.targetpolicies import TargetPolicy
from app.core.services import targetpolicies
from app.core.services.deployment import DeploymentParameters, TargetPolicyDeploymentService, ClusterDeploymentService, AppDeploymentService
from app.core.services.manifest import ArgoCDDeploymentManifestGenerator
from app.utils.enums import EventType
from app.utils.enums import OnboardStatus

log = getLogger(__name__)

settings = get_settings()


class Operations(ABC):
    @abstractmethod
    async def create_deployment_obj(self):
        pass


class Onboarder(Operations, ABC):
    """Responsible for onboarding of targetpolicy, cluster and application. It defines a single onboard method that
    takes of generating appropriate objects, files and checkin of those files in Git and objects in DB"""
    def __init__(self, user):
        self.user = user
        self.manifest_generator = ArgoCDDeploymentManifestGenerator()

    async def onboard(self):
        try:
            deployment_obj = await self.create_deployment_obj()
            if deployment_obj:
                success = await self.manifest_generator.generate_and_checkin_manifests(deployment_obj, self.user)
                if not success:
                    return OnboardStatus.FAILURE
            return OnboardStatus.COMPLETED
        except Exception as e:
            log.error(f"Error in onboarding {type(self)} due to {str(e)}")
            return OnboardStatus.FAILURE


class TargetPolicyOnboarder(Onboarder):
    def __init__(self, target_policy: TargetPolicy, user):
        super().__init__(user)
        self.target_policy = target_policy
        self.deployment_service = TargetPolicyDeploymentService(operation=self.target_policy.operation)
        self.user = user

    async def create_deployment_obj(self):
        return await self.deployment_service.create_deployment_object(
            DeploymentParameters(user=self.user, targetPolicy=self.target_policy))


class ClusterOnboarder(Onboarder):
    def __init__(self, cluster: Cluster, user):
        super().__init__(user)
        self.cluster = cluster
        self.deployment_service = ClusterDeploymentService()
        # Clusters can't be deleted as of now without target policy
        self.user = user

    async def create_deployment_obj(self):
        affected_target_policies = await targetpolicies.fetch_affected_target_policies(
            self.cluster.metadata, EventType.CLUSTER_ONBOARDING
        )
        log.debug(
            f"Fetched Affected TargetPolicies: {affected_target_policies} for Cluster with name: {self.cluster.name}")
        if len(affected_target_policies) > 0:
            deployment_obj = await self.deployment_service.create_deployment_object(DeploymentParameters(user=self.user, targetPolicy=affected_target_policies, cluster=self.cluster))
            if deployment_obj:
                return deployment_obj

        await ClusterState.upsert_cluster_state(self.cluster.id, self.cluster, [])
        return self.cluster



class ApplicationOnboarder(Onboarder):
    def __init__(self, application, user):
        super().__init__(user)
        self.application = application
        self.deployment_service = AppDeploymentService()
        self.user = user

    async def create_deployment_obj(self):
        affected_target_policies = await targetpolicies.fetch_affected_target_policies(
            self.application.metadata, EventType.APP_ONBOARDING
        )
        log.info(
            f"Fetched Affected TargetPolicies: {affected_target_policies} for application with name: {self.application.name}")
        if len(affected_target_policies) > 0:
            return await self.deployment_service.create_deployment_object(
                DeploymentParameters(user=self.user, targetPolicy=affected_target_policies, application=self.application)
            )
        else:
            return None
