from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.find.evaluation import RegEx

from app.core.auth.user import User
from app.core.config import get_settings
from app.core.models.namespaces import Namespace

settings = get_settings()


async def get_authorized_namespace_by_name(user, namespace_name):
    return await _get_authorized_namespace(user, namespace_name=namespace_name)


async def get_authorized_namespace_by_names(user, namespace_names):
    return await _get_authorized_namespace(user, namespace_names=namespace_names)


# TODO: Refactor this- duplicate code
async def _get_authorized_namespace(user, namespace_id=None, namespace_name=None, namespace_names=None):
    admin_roles_list = user.get_admin_roles()
    if len(admin_roles_list) != 0:
        return await search_by_env_for_admin(admin_roles_list, namespace_id, namespace_name, namespace_names)
    user_groups = user.role_collection.get_in_group_format()
    groups = [role.rsplit('-', 1)[0] for role in user_groups]
    if namespace_id is None and namespace_name is None:
        if len(user_groups) == 0:
            return []
        return await Namespace.find(In(Namespace.group, groups)).to_list()
    elif namespace_name is None:
        return await Namespace.find_one(Namespace.id == namespace_id, In(Namespace.group, groups))
    elif namespace_names is None:
        return await Namespace.find_one(Namespace.name == namespace_name, In(Namespace.group, groups))
    else:
        return Namespace.find(In(Namespace.name, namespace_names), In(Namespace.group, groups))


async def search_by_env_for_admin(admin_roles_list, namespace_id, namespace_name, namespace_names):
    group_separator = settings.GROUP_NAME_SEPARATOR
    environments = '|'.join([f'{group_separator}{role.env}' for role in admin_roles_list])
    if namespace_id is None:
        namespaces = await Namespace.find(RegEx(Namespace.group, environments)).to_list()
        return namespaces
    elif namespace_name is None and namespace_names is None:
        return await Namespace.find_one(Namespace.id == namespace_id,
                                        RegEx(Namespace.group, environments))
    elif namespace_names is None and namespace_name is not None:
        return await Namespace.find_one(Namespace.name == namespace_name,
                                        RegEx(Namespace.group, environments))
    else:
        return Namespace.find(In(Namespace.name, namespace_names),
                              RegEx(Namespace.group, environments))


async def get_all_namespaces(user: User):
    return await _get_authorized_namespace(user)


async def is_part_of_namespace_group(user, namespace_name):
    namespace = await get_authorized_namespace_by_name(user=user, namespace_name=namespace_name)
    if namespace is not None:
        return True
    return False
