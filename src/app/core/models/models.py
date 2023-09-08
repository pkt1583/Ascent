from typing import List

import motor
from beanie import init_beanie

from .applications import Application
from .clusters import Cluster
from .clusterstate import ClusterState
from .deployment import Deployment
from .namespaces import Namespace
from .targetpolicies import TargetPolicy

__beanie_models__ = {"application": Application, "cluster": Cluster, "namespace": Namespace,
                     "targetpolicy": TargetPolicy, "deployment": Deployment, "clusterstate": ClusterState
                    }

from ...utils.common import popualate_env_cache


def get_model(name: str):
    return __beanie_models__.get(name)


async def init_odm(settings):
    client = motor.motor_asyncio.AsyncIOMotorClient(
        settings.AZURE_COSMOS_CONNECTION_STRING
    )

    await init_beanie(
        database=client[settings.AZURE_COSMOS_DATABASE_NAME],
        document_models=__beanie_models__.values(),
    )


async def init_env_cache(env: List[str] = None):
    env = await Cluster.distinct("environment")
    await popualate_env_cache(env)
    groups_envs = await Namespace.distinct("group")
    await popualate_env_cache([groups_env.split("-")[-1] for groups_env in groups_envs])
