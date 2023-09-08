import atexit
import logging
import os
import shutil

from testcontainers.mongodb import MongoDbContainer

import tests.common.common
from app.core.config import get_settings
from app.utils import git_handler
from app.utils.git_handler import GitManager
from tests.common.common import temp_dir_name, commit_dir_path, delete_temp_on_exit
from tests.steps import utils

LOCALHOST_IP = "127.0.0.1"

settings = get_settings()
settings.FEATURE_RBAC_ENABLED = True
# so that auth logic runs against fake tokens
is_running_end_to_end = os.environ.get("IS_RUNNING_END_TO_END", "false").lower() == "true"
base_url_for_end_to_end = os.environ.get("BASE_URL_FOR_E2E")
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)

os.environ.setdefault("TC_HOST", LOCALHOST_IP)  # https://github.com/testcontainers/testcontainers-python/issues/99
mongocontainer = MongoDbContainer(image="mongo:6.0.5")


def init_mongo():
    mongocontainer.start()
    connection_url = mongocontainer.get_connection_url()
    print(connection_url)
    os.environ.setdefault('AZURE_COSMOS_CONNECTION_STRING', connection_url)
    settings.AZURE_COSMOS_CONNECTION_STRING = connection_url
    print("Mongo server started")


def mark_for_deletion(context, collection_name: str, to_be_deleted_id: str):
    context.deletion_map.setdefault(collection_name, []).append(to_be_deleted_id)


def after_all(context):
    if not is_running_end_to_end:
        mongocontainer.stop()


def before_all(context):
    context.deletion_map = {}
    settings.WEBSITE_AUTH_ENABLED = True
    settings.CP_AUTH_BYPASS_ENV = "nonprod"
    tests.common.common.commit_dir_path = commit_dir_path
    if not is_running_end_to_end:
        init_mongo()
    else:
        utils.clean_up_db(settings.AZURE_COSMOS_DATABASE_NAME)
    if os.path.exists(temp_dir_name):
        delete_temp_on_exit()
    os.makedirs(temp_dir_name)
    atexit.register(delete_temp_on_exit)
    context.c_headers = {}


class FakeGitManager(GitManager):
    def __init__(self, repo_url, local_folder, branch_name):
        self.local_folder = local_folder
        self.repo = None
        self.checkout()

    def clone_repo(self):
        pass

    def checkout(self, *args):
        if tests.common.common.checkout_dir_path is not None and os.path.exists(tests.common.common.checkout_dir_path):
            shutil.copytree(tests.common.common.checkout_dir_path, self.local_folder, dirs_exist_ok=True)
            tests.common.common.checkout_dir_path = None

    def commit_and_push(self, *args):
        if os.path.exists(commit_dir_path):
            shutil.rmtree(commit_dir_path)
        shutil.copytree(self.local_folder, commit_dir_path)
        return True

    def create_pull_request(self, feature_branch: str, title: str, description: str):
        pass


if not is_running_end_to_end:
    git_handler.GitManager = FakeGitManager
