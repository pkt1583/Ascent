import os
from logging import getLogger

import git
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from requests.utils import unquote
from app.core.auth.user import User

from app.core.config import get_settings
settings = get_settings()

log = getLogger(__name__)


def get_pat() -> str:
    try:
        return os.getenv('AZURE_DEVOPS_PAT')
    except KeyError:
        log.info("PAT token not found")
        raise KeyError


def get_git_url(repo_url: str = None):
    if repo_url is None:
        repo_url = settings.ARGOCD_MASTER_APPLICATION_REPO_URL
    return repo_url.replace("https://", f"https://{get_pat()}@")


class GitManager:
    logger = getLogger(__name__)

    def __init__(self, repo_url, local_folder, branch_name):
        self.repo_url = repo_url
        self.local_folder = local_folder
        self.repo = None
        self.branch_name = branch_name
        self.clone_repo()
        self.checkout()

    def clone_repo(self):
        try:
            self.repo = git.Repo.clone_from(
                self.repo_url, self.local_folder, depth=1)
            self.logger.info(f"Repo {self.repo_url} cloned successfully.")

        except Exception as ex:
            self.logger.error(
                f"Error cloning repository {self.repo_url}: {ex}")
            raise ex

    def checkout(self, branch_name: str = None):
        try:
            repo = git.Repo(self.local_folder)
            branch = repo.create_head(
                branch_name if branch_name else self.branch_name)
            branch.checkout()

            if branch_name is None:
                repo.git.pull('origin', self.branch_name)

        except Exception as ex:
            self.logger.error(
                f"Error checkinout out branch {branch_name if branch_name else self.branch_name}: {ex}")
            raise ex

    def commit_and_push(self, commit_msg, branch_name: str = None, user: User = None):
        self.logger.info("Committing and pushing the manifest files to git")
        try:
            if self.repo.is_dirty(untracked_files=True):
                self.repo.config_writer().set_value("user", "name", user.name).release()
                self.repo.config_writer().set_value("user", "email", user.claims["email"]).release()
                self.repo.git.add('.')
                self.repo.git.commit('-m', commit_msg)
                push_results = self.repo.remotes.origin.push(
                    refspec=f'refs/heads/{branch_name if branch_name else self.branch_name}')

                for info in push_results:
                    if info.flags & (info.ERROR | info.REJECTED):
                        self.logger.error(
                            f"Error pushing ref {info.local_ref} to {info.remote_ref}")
                        # ToDo : shouldn't we raise exception here?
                        return False
                    else:
                        self.logger.info(
                            f"Ref {info.local_ref} was successfully pushed to {info.remote_ref}")
                self.logger.info("Files committed and pushed successfully.")
            else:
                self.logger.info("No changes to commit and push.")
            return True

        except Exception as ex:
            self.logger.error(f"Error committing and pushing files: {str(ex)}")
            raise ex

    def create_pull_request(self, feature_branch: str, title: str, description: str):
        try:
            # Extract the organization URL
            organization_url = f"https://{('/'.join(self.repo_url.split('/')[:4])).split('@')[1]}"

            # Extract the project name and repository name
            path_parts = self.repo_url.split('/')[4:]
            project_name = unquote(path_parts[0])
            repository_name = path_parts[2]

            # Create a connection to Azure DevOps
            credentials = BasicAuthentication('', get_pat())
            connection = Connection(
                base_url=organization_url, creds=credentials)

            # Get the Git client
            git_client = connection.clients.get_git_client()

            # Create the pull request parameters
            pr_parameters = {
                'source_ref_name': f'refs/heads/{feature_branch}',
                'target_ref_name': f'refs/heads/{self.branch_name}',
                'title': title,
                'description': description
            }

            # Create the pull request
            pull_request = git_client.create_pull_request(
                pr_parameters, repository_name, project=project_name)

            if pull_request:
                self.logger.info('Pull request created successfully!')
                pr_url = f"{pull_request.repository.web_url}/pullrequest/{str(pull_request.pull_request_id)}"
                self.logger.info(f'Pull request URL:{pr_url}')
            else:
                raise Exception("Failed to create pull request.")

        except Exception as ex:
            self.logger.error(f"Error creating PR: {ex}")
            raise ex

    def delete_branch(self, branch_name: str):
        remotes = self.repo.remotes
        origin_exists = any(remote.name == 'origin' for remote in remotes)

        if origin_exists:
            for remote in remotes:
                branches = remote.refs
                branch_exists = any(
                    branch.name == f"refs/remotes/{remote.name}/{branch_name}" for branch in branches)

                if branch_exists:
                    remote.push(refspec=f":{branch_name}")
                    self.logger.info(
                        f"Branch {branch_name} deleted successfully from remote {remote.name}")
                    break
            else:
                self.logger.warning(
                    f"Branch {branch_name} does not exist in any remote for deletion")
        else:
            self.logger.warning("Remote 'origin' does not exist")


def initialize_git_manager(repo_url: str, local_folder: str, branch_name: str) -> GitManager:
    return GitManager(get_git_url(repo_url), local_folder, branch_name)
