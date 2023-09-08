from app.core.config import get_settings

settings = get_settings()

class RoleHierarchy:
    def __init__(self, name):
        self.name = name
        self.implicit_permissions = []

    # implement a method that allows a role to provide implicit permissions to other roles using variadic arguments
    def provide_implicit_permissions(self, *roleheirarchies):
        for hierarchy in roleheirarchies:
            self.implicit_permissions.append(hierarchy)

    def __repr__(self):
        return f"{self.name}"

    # implement a method that returns a list of all the permissions that a role has
    def get_all_implicit_permissions(self):
        permissions = []
        permissions.extend(self.implicit_permissions)
        return permissions


admin_role = RoleHierarchy(settings.ADMIN_ROLE_NAME)
contributor_role = RoleHierarchy(settings.CONTRIBUTOR_ROLE_NAME)
reader_role = RoleHierarchy(settings.READER_ROLE_NAME)
admin_role.provide_implicit_permissions(contributor_role, reader_role)
contributor_role.provide_implicit_permissions(reader_role)


class Role:
    def __init__(self, app_name, env, role):
        self.app_name = app_name
        self.env = env
        self.role_type = role

    def __repr__(self):
        return f"Role(app_name='{self.app_name}', env='{self.env}', role='{self.role_type}')"

    def get_role_in_group_format(self):
        return f"{self.app_name}-{self.env}-{self.role_type}"


class RoleCollection:
    def __init__(self):
        self.roles = []

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        self.roles.extend(roles)

    def get_rbac_by_type(self, role_type):
        return {role.role_type: [role for role in self.roles if role.role_type == role_type] for role in self.roles if
                role.role_type == role_type}

    def get_in_group_format(self, role_type=None):
        return [role.get_role_in_group_format() for role in self.roles if
                role_type is None or role.role_type == role_type]

    # This is without reader/contributor
    def get_role_in_namespace_group_format(self):
        return {f"{role.app_name}-{role.env}" for role in self.roles}

    def get_rbac_by_env_and_type(self, env, role_type):
        roles = []
        for role in self.roles:
            if role.env == env and role.role_type == role_type:
                roles.append(role)
        return roles

    async def get_environments(self):
        return {role.env for role in self.roles}

    def __repr__(self):
        return f"RoleCollection(roles={self.roles})"

def add_additional_permissions_based_on_hierarchy(role: Role):
    all_roles = [Role(role.app_name, role.env, role.role_type)]
    role_type_map = {
        settings.ADMIN_ROLE_NAME: admin_role,
        settings.CONTRIBUTOR_ROLE_NAME: contributor_role,
        settings.READER_ROLE_NAME: reader_role
    }
    if role.role_type in role_type_map:
        for permission in role_type_map[role.role_type].get_all_implicit_permissions():
            all_roles.append(Role(role.app_name, role.env, permission.name))
    return all_roles



