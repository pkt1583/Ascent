import re
from typing import Optional

from jose import ExpiredSignatureError, jwt
from jose.exceptions import JWSSignatureError

from app.core.auth.exception import UnAuthorizedException, AccessTokenMissingException, IdTokenMissingException
from app.core.auth.http.appservice import AppServiceBasedTokenProvider
from app.core.auth.rbac import RoleCollection, Role, add_additional_permissions_based_on_hierarchy
from app.core.auth.token import TokenProvider, log, IdAndAccessToken, settings, TokenService
from app.core.auth.token_stub import DummyTokenProvider
from app.core.auth.user import User
from app.core.config import get_settings
from app.utils import is_valid_role, retryable_requester
from app.utils.common import env_cache

signing_keys = {}

settings = get_settings()

def populate_signing_keys():
    if settings.AZURE_TENANT_ID is None or settings.AZURE_CLIENT_ID is None:
        raise Exception("Authentication enabled service needs tenant_id and client_id")
    jwks_uri = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/discovery/v2.0/keys"
    jwks_response = retryable_requester().get(jwks_uri).json()
    return {key['kid']: key for key in jwks_response['keys'] if
            key['kty'] == 'RSA' and key.get('alg', 'RS256') == 'RS256'}


if settings.WEBSITE_AUTH_ENABLED:
    signing_keys = populate_signing_keys()


def is_token_issued_by_app_registration(decoded_token):
    # Indicates how the client was authenticated. For a public client, the value is "0".
    # If client ID and client secret are used, the value is "1".
    # If a client certificate was used for authentication, the value is "2"
    client_auth = decoded_token.get("azpacr")
    azure_service_principal = decoded_token.get("azp")
    return client_auth == "1" and azure_service_principal == settings.AZURE_CLIENT_ID


class DefaultTokenService(TokenService):
    def __init__(self, token_provider: TokenProvider):
        self.token_provider = token_provider

    def get_token_provider(self) -> TokenProvider:
        return self.token_provider

    async def __decode(self, **kwargs) -> Optional[User]:
        token_provider: TokenProvider = self.get_token_provider()
        try:
            return await self.__decode_token(token_provider.get_id_and_access_token(**kwargs))
        except ExpiredSignatureError:
            log.warning("Access token expired, trying to get a new one using the refresh token")
            return await self.__decode_token(token_provider.renew_token(**kwargs))

    async def __decode_token(self, tokens: IdAndAccessToken) -> Optional[User]:
        is_super_reader_user = False
        if tokens.access_token is None:
            raise AccessTokenMissingException("Required Access token is missing")
        if tokens.id_token is None:
            decoded_token = self.decode_id_or_access_token(tokens.access_token)
            """In case the token is issued by app registration using client secret (non interactive flows) the id token is not issued
            in such case we assume that the call is through automated system and we validate that the token is issued 
            in non interactive flow. We validate that the token is issued for valid service principal and then mark the
            user as super user for read access"""
            if (is_token_issued_by_app_registration(decoded_token)):
                is_super_reader_user = True
            else:
                raise IdTokenMissingException("Id token is required")
        else:
            decoded_token = self.decode_id_or_access_token(tokens.id_token)

        groups = decoded_token.get(settings.GROUP_NODE_IN_DECODED_TOKEN, [])
        role_collection = RoleCollection()
        for group in groups:
            match = re.match(settings.GROUP_PATTERN, group)
            if match:
                role = match.group(3)
                if is_valid_role(role):
                    role_obj = Role(match.group(1), match.group(2), role)
                    role_collection.add_roles(add_additional_permissions_based_on_hierarchy(role_obj))
                else:
                    log.warning("Invalid group %s found for user that will be ignored", group)
        if not settings.FEATURE_RBAC_ENABLED:
            # rbac not enabled but auth enabled stub to admin role
            # Stubbing will be only for DEV
            admin_role = Role(app_name=settings.CP_APP_NAME, env=settings.CP_AUTH_BYPASS_ENV,
                              role=settings.ADMIN_ROLE_NAME)

            role_collection.add_role(admin_role)
        user = User(claims=decoded_token, id_token=tokens.id_token, access_token=tokens.access_token,
                    role_collection=role_collection, name=decoded_token.get("name", "unknown"))
        if is_super_reader_user:
            for env_name in env_cache:
                role_collection.add_role(
                    Role(app_name=settings.CP_APP_NAME, env=env_name, role=settings.ADMIN_ROLE_NAME))
            user.is_super_reader = True
        return user

    def decode_id_or_access_token(self, received_token):
        header: dict[str, str] = jwt.get_unverified_header(token=received_token) or {}
        token = jwt.get_unverified_claims(token=received_token)
        if settings.IS_ON_APP_SERVICE and settings.WEBSITE_AUTH_ENABLED:
            try:
                token = self.__validate_and_decode(header, received_token)
            except JWSSignatureError as e:
                # signature verification failed. Possibly signing key has rotated. Try to refresh signatures once
                global signing_keys
                signing_keys = populate_signing_keys()
                token = self.__validate_and_decode(header, received_token)
        return token

    def __validate_and_decode(self, header, token):
        signing_key = signing_keys.get(header['kid'])
        token = jwt.decode(token=token, key=signing_key, algorithms=['RS256'],
                           audience=settings.AZURE_CLIENT_ID)  # type: ignore
        return token

    async def decode_and_check_authorization(self, expected_roles, **kwargs) -> User:
        user = await self.__decode(**kwargs)
        if user.is_authorized(expected_roles):
            return user
        raise UnAuthorizedException(
            message=f"Not authorized. You need to be a member of the {expected_roles} roles. Your "
                    f"current roles are {user.role_collection}.", expected_roles=expected_roles,
            user_roles=user.role_collection.roles)


def get_token_service():
    token_provider = AppServiceBasedTokenProvider() if settings.WEBSITE_AUTH_ENABLED else DummyTokenProvider()
    token_service = DefaultTokenService(token_provider)
    return token_service
