from app.core.auth.rbac import RoleCollection, settings


class User:

    def __init__(self, id_token: str = None, name: str = None, access_token: str = None, role_collection=None,
                 claims=[]) -> None:
        self.claims = claims
        self.name = name
        self.access_token = access_token
        self.id_token = id_token
        self.role_collection = role_collection or RoleCollection()
        self.is_super_reader = False

    def get_admin_roles(self):
        admin_roles = self.role_collection.get_rbac_by_type(settings.ADMIN_ROLE_NAME)
        return admin_roles[settings.ADMIN_ROLE_NAME] if admin_roles else admin_roles

    def is_plat_admin(self):
        for role in self.role_collection.roles:
            if role.role_type.lower() == settings.ADMIN_ROLE_NAME:
                return True
        return False

    def is_authorized(self, roles):
        return not settings.FEATURE_RBAC_ENABLED or self.is_plat_admin() or all(
            self.role_collection.get_rbac_by_type(role) for role in roles)
