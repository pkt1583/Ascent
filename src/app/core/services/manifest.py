import logging
import os.path
import tempfile
from abc import ABC, abstractmethod
from logging import getLogger
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.core.config import get_settings
from app.core.models.clusters import Cluster
from app.core.models.clusterstate import ClusterState
from app.core.models.deployment import Deployment
from app.core.schemas.deployment import DeploymentState
from app.core.services import OperationRegistry, template
from app.utils import git_handler
from app.utils.common import find_delta_items
from app.utils.constants import (
    TEMPLATES_BASE_PATH, KUSTOMIZE_TEMPLATE_NAME,
    ARGOCD_APPLICATION_TEMPLATE_NAME, ARGOCD_PROJECT_NAME,
    ARGOCD_MASTER_FILE_NAME, ARGOCD_APPLICATION_FILE_SUFFIX,
    KUSTOMIZE_FILE_NAME, MANIFESTS_GIT_BRANCH, GIT_COMMIT_MESSAGE)
from app.utils.manifest import prepare_consumer_application_data, prepare_master_application_data
from app.utils.template import JinjaTempalte

logger = logging.getLogger(__name__)

settings = get_settings()


def get_argocd_application_file_name(app, cluster, output_directory):
    environment = cluster.environment if cluster.environment else "nonprod"
    argocd_application_output_dir = f"{output_directory}/{cluster.name}/consumer/environment/{environment}"
    application_file_name = f"{app.name}{ARGOCD_APPLICATION_FILE_SUFFIX}"
    return application_file_name, argocd_application_output_dir


def generate_kustomize_data(cluster, mappings):
    """
    Generates Kustomize data for the specified cluster to app mappings.
    Args:
        mappings (Mappings): An instance of the Mappings class containing information about the applications.
    Returns:
        dict: A dictionary containing the generated Kustomize data.
    Raises:
        ValueError: If the mappings argument is not provided.
    """
    if not mappings:
        raise ValueError("The mappings argument cannot be empty or None.")

    kustomize_items = {}
    kustomize_items[cluster.environment] = []
    for app in mappings.applications:
        kustomize_items[cluster.environment].append(
            {'name': f"{app.name}{ARGOCD_APPLICATION_FILE_SUFFIX}"})
    return kustomize_items


def generate_kustomize_file(project_name, cluster_name, kustomize_items, output_directory, template):
    """
    Generates a Kustomization file for the specified project, cluster and Kustomize items.

    Args:
        project_name (str): The name of the project.
        cluster_name (str): The name of the target cluster.
        kustomize_items (dict): A dictionary containing the Kustomize items to include in the file.

    Returns:
        None

    Raises:
        ValueError: If either the project_name, cluster_name or kustomize_items argument is not provided.
    """

    if not project_name:
        raise ValueError(
            "The project_name argument cannot be empty or None.")
    if not cluster_name:
        raise ValueError(
            "The cluster_name argument cannot be empty or None.")
    if not kustomize_items:
        raise ValueError(
            "The kustomize_items argument cannot be empty or None.")

    output_dir = f"{output_directory}/{cluster_name}/consumer"
    logger.info(
        f"Generating Kustomize file for {cluster_name}at  {output_dir} with items - {kustomize_items}")
    return template.render(f"{TEMPLATES_BASE_PATH}/{KUSTOMIZE_TEMPLATE_NAME}", output_dir, KUSTOMIZE_FILE_NAME,
                           {'shortProjectName': project_name, 'items': kustomize_items})


class ManifestGenerator(ABC):
    async def generate_and_checkin_manifests(self, deployment_obj=None, user=None) -> bool:
        try:
            template_obj = template.init_template()

            with tempfile.TemporaryDirectory() as manifest_output_directory:
                # Use module name here to monkeypatch
                git_manager = git_handler.initialize_git_manager(settings.ARGOCD_MASTER_APPLICATION_REPO_URL,
                                                                 manifest_output_directory, MANIFESTS_GIT_BRANCH)

                is_manifest_generated = await self._generate(deployment_obj, template_obj,
                                                             f"{manifest_output_directory}/{ARGOCD_PROJECT_NAME}")

                if not is_manifest_generated:
                    logger.info(f"Unable to generate manifest files for {type(deployment_obj)}-{deployment_obj}")
                    return False
                else:
                    return git_manager.commit_and_push(GIT_COMMIT_MESSAGE, MANIFESTS_GIT_BRANCH, user)
        except Exception as e:
            logger.error(f"Error in generating and pushing files due to {str(e)}")
            return False

    @abstractmethod
    async def _generate(self, deployment: Deployment, template: JinjaTempalte, path: str):
        raise NotImplemented("Concrete implementation missing")


class ArgoCDDeploymentManifestGenerator(ManifestGenerator):

    def __init__(self):
        self.logger = getLogger(__name__)

    async def _generate(self, deployment: Deployment, template: JinjaTempalte, path: str) -> bool:
        return await self.generate_manifest_for_deployment(deployment, template, path)

    async def generate_manifest_for_deployment(self, deployment: Deployment, template: JinjaTempalte,
                                               output_directory: str) -> bool:
        """
        Generates the ArgoCD manifest for a deployment.

        It iterates over all the clusters in the deployment, gets the applications
        from it and compares them with the applications for that cluster in the database.
        It generates the manifest only for newly added applications, saves it back to
        the database, and generates the kustomize file for all the applications.

        Returns:
            The method does not return anything.
        """
        self.logger.info(
            f"Generating the ArgoCD manifest for {deployment}")
        for deployment_manifest_operation in OperationRegistry.get_instance().get_operations():
            if deployment_manifest_operation.can_process(deployment):
                operation_status = await deployment_manifest_operation.perform(deployment, template,
                                                                               output_directory)
                if operation_status == False:
                    return False
        return True

class ManifestOperation(ABC):

    @abstractmethod
    async def perform(self, received_model,
                      template: JinjaTempalte, output_dir: str) -> bool:
        """Either adds manifest or removes manifest"""

    @abstractmethod
    def can_process(self, deploymentOrCluster) -> bool:
        """Check if it can process the deployment state"""

    def render_manifest(self, cluster, data, output_dir, output_file_name, template: JinjaTempalte):
        """
       Renders manifest as per data.
        """

        return template.render(f"{TEMPLATES_BASE_PATH}/{ARGOCD_APPLICATION_TEMPLATE_NAME}", output_dir,
                               output_file_name,
                               data)


class ClusterManifestAddOperation(ManifestOperation):
    """This will be called when Cluster manifest generation is triggered. It generates master manifest files"""
    def __init__(self):
        self.logger = getLogger(__name__)

    async def perform(self, cluster: Cluster, template: JinjaTempalte, output_dir: str) -> bool:
        """
               Generates the ArgoCD manifest on onboarding a new cluster.

               Returns:
                   The method does not return anything.
               """
        self.logger.info(
            f"Generating the ArgoCD manifest for {cluster}")
        argocd_master_application_output_dir = f"{output_dir}/{cluster.name}/consumer/argocd/"
        master_application_template_data = prepare_master_application_data(
            ARGOCD_PROJECT_NAME, cluster.name)
        # Generate argocd master application manifest
        self.render_manifest(
            cluster, master_application_template_data, argocd_master_application_output_dir, ARGOCD_MASTER_FILE_NAME, template)

        return True

    def can_process(self, received_model: [Cluster | Deployment]) -> bool:
        return isinstance(received_model, Cluster)


OperationRegistry.get_instance().add_operation(ClusterManifestAddOperation())


class DeploymentManifestOperation(ManifestOperation):
    async def perform(self, deployment: Deployment, template: JinjaTempalte, output_dir: str) -> bool:
        for cluster_id, deployment_state in deployment.deployment_mappings.items():
            if not await self._process_for_each_cluster(deployment.target_policy_id, cluster_id, deployment_state, template, output_dir):
                return False
        return True

    @abstractmethod
    async def _process_for_each_cluster(self, target_policy_id: str, cluster_id: str, deployment_state: DeploymentState,
                                        template: JinjaTempalte, output_dir: str):
        raise NotImplemented("Need concrete implementation")


class DeploymentManifestAddOperation(DeploymentManifestOperation):

    def __init__(self):
        self.logger = getLogger(__name__)

    async def _process_for_each_cluster(self, target_policy_id: str, cluster_id: str, deployment_state: DeploymentState,
                                        template: JinjaTempalte, output_dir: str):
        """
        Generates the ArgoCD manifest for a deployment.

        It iterates over all the clusters in the deployment, gets the applications
        from it and compares them with the applications for that cluster in the database.
        It generates the manifest only for newly added applications, saves it back to
        the database, and generates the kustomize file for all the applications.

        Returns:
            The method does not return anything.
        """
        self.logger.info(
            f"Generating the ArgoCD manifest for {target_policy_id}")

        self.logger.info(
            f"Creating application mappings for the cluster - {cluster_id}")

        cluster = deployment_state.cluster_context

        # Get the applications for the cluster from the database and compare them with the new applications
        cluster_state_obj = await ClusterState.find_one(ClusterState.cluster._id == cluster_id)
        if not cluster_state_obj:
            cluster_state_obj = ClusterState(
                id=str(uuid4()), cluster=cluster, applications=deployment_state.add)
            delta_apps = deployment_state.add
        else:
            delta_apps = find_delta_items(
                deployment_state.add, cluster_state_obj.applications, key=lambda item: item.id)
            cluster_state_obj.applications += delta_apps

        # Save the cluster state to the database.
        if not await cluster_state_obj.save():
            return False

        # Generate the argocd & kustomizes file for all the applications.
        self.__generate_argocd_manifests(
            cluster_state_obj.applications, cluster, target_policy_id, output_dir, template)
        kustomize_template_data = generate_kustomize_data(
            cluster, cluster_state_obj)
        generate_kustomize_file(
            ARGOCD_PROJECT_NAME, cluster.name, kustomize_template_data, output_dir, template)

        return True

    def __generate_argocd_manifests(self, apps, cluster, target_policy_id, output_directory, template: JinjaTempalte):
        """
        Generate ArgoCD manifests for a given application on a specified cluster.

        Args:
        app (ApplicationResponse): An instance of the ApplicationResponse containing information about the application.
        cluster (ClusterResponse): An instance of the ClusterResponse class representing the target cluster.
        target_policy_id (str): Target policy id

        Returns:
        None

        Raises:
        ValueError: If either the app or cluster argument is not provided.

        Notes:
        This method generates ArgoCD manifests for the specified application on the specified cluster.
        It calls two private methods, __generate_application_manifests() and __generate_master_application_manifests(),
        to create the necessary manifests. The generated manifests are used to deploy the application using ArgoCD.
        """
        if not apps:
            raise ValueError("The app argument cannot be empty or None.")
        if not cluster:
            raise ValueError("The cluster argument cannot be empty or None.")
        for app in apps:
            application_file_name, argocd_application_output_dir = get_argocd_application_file_name(app, cluster,
                                                                                                    output_directory)

            consumer_application_template_data = prepare_consumer_application_data(
                app, cluster, target_policy_id)
            # for each app create application manifest
            self.render_manifest(
                cluster, consumer_application_template_data, argocd_application_output_dir, application_file_name,
                template)

        argocd_master_application_output_dir = f"{output_directory}/{cluster.name}/consumer/argocd/"
        master_application_template_data = prepare_master_application_data(
            ARGOCD_PROJECT_NAME, cluster.name)
        # Generate argocd master application manifest
        self.render_manifest(
            cluster, master_application_template_data, argocd_master_application_output_dir, ARGOCD_MASTER_FILE_NAME,
            template)

    def can_process(self, deployment: [Deployment | Cluster]) -> bool:
        if isinstance(deployment, Deployment):
            # Any add found then this processor should run
            for cluster_id, deployment_state in deployment.deployment_mappings.items():
                if deployment_state.add is not None and len(deployment_state.add) != 0:
                    return True
        return False


class DeploymentManifestRemoveOperation(DeploymentManifestOperation):
    def __init__(self):
        self.logger = getLogger(__name__)

    async def _process_for_each_cluster(self, target_policy_id: str, cluster_id: str, deployment_state: DeploymentState,
                                        template: JinjaTempalte, output_dir: str):
        self.logger.info(
            f"Removing the ArgoCD manifest for {target_policy_id}")
        cluster = deployment_state.cluster_context
        cluster_state_obj = await ClusterState.find_one(Eq(ClusterState.cluster._id, cluster_id))

        if not cluster_state_obj:
            self.logger.warning(
                f"{[apps.name for apps in deployment_state.purge]} were never deployed on {cluster.name}")
        else:
            await self._remove_app_from_cluster_state(cluster, cluster_state_obj, deployment_state, output_dir, template)
        return True

    def can_process(self, deployment: [Deployment | Cluster]) -> bool:
        if isinstance(deployment, Deployment):
            for cluster_id, deployment_state in deployment.deployment_mappings.items():
                if deployment_state.purge is not None and len(deployment_state.purge) != 0:
                    return True
        return False

    async def _remove_app_from_cluster_state(self, cluster, cluster_state: ClusterState,
                                             deployment_state: DeploymentState,
                                             output_directory, template):
        """This removes app from the cluster state object, delete the app manifest from argocd_application_output_dir and saves back cluster state.
        In case yaml files are not found in output dir (will happen only if anyone has manually delete application) then it throws warning"""
        for application in deployment_state.purge:
            if len(cluster_state.applications) == 0:
                self.logger.warning(f"Cluster {cluster_state.cluster.name} is not having any application.")
                continue
            cluster_state.applications = [app for app in cluster_state.applications if app.name != application.name]
            self.logger.info(f"Removed {application} from cluster state for cluster {cluster_state.cluster.name}")
            application_file_name, argocd_application_output_dir = get_argocd_application_file_name(application,
                                                                                                    cluster,
                                                                                                    output_directory)
            application_file_path = os.path.join(argocd_application_output_dir, application_file_name)
            if os.path.exists(application_file_path):
                os.remove(application_file_path)
                self.logger.info(f"Removed {application_file_path}")
            else:
                logger.warning(f"Manifest {application_file_path} not found for removal")
        kustomize_template_data = generate_kustomize_data(
            cluster, cluster_state)
        generate_kustomize_file(
            ARGOCD_PROJECT_NAME, cluster.name, kustomize_template_data, output_directory, template)

        await cluster_state.save()


OperationRegistry.get_instance().add_operation(DeploymentManifestRemoveOperation(), DeploymentManifestAddOperation())



