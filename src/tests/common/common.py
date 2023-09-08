import asyncio
import os
import shutil
import tempfile

from app.core.config import get_settings
from app.core.models.models import init_odm

temp_dir_name = "bdd-staging_manifest"
commit_dir_path = os.path.join(tempfile.gettempdir(), "commit-dir")
checkout_dir_path = None
tokens = {}
settings = get_settings()


def ready_db_object_for_query(context=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop=loop)
    # Reinit so that it takes new coroutine context, else it will work on async context of testclient that has closed
    loop.run_until_complete(init_odm(settings=settings))
    return loop


def delete_temp_on_exit():
    shutil.rmtree(temp_dir_name)


def common_headers(context):
    # This header will be used when running against app deployed in Azure
    return {}  # Placeholder for future
