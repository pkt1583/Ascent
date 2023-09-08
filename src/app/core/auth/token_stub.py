import datetime
import logging

from jose import jwt

from app.core.auth.token import TokenProvider, IdAndAccessToken
from app.core.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


class DummyTokenProvider(TokenProvider):
    """Provides token when the application is not backed by any auth. This primarily created to that rest of
    application code is abstracted out from knowing if they are behind auth or no. It will give Admin role for
    CP_AUTH_BYPASS_ENV. This should never be initialized in production as prod is expected to always have auth"""
    def get_id_and_access_token(self, **kwargs) -> IdAndAccessToken:
        payload_for_access_token = {
            'user_id': "Dummy",
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iss': settings.AZURE_TENANT_ID,
            'audience': settings.AZURE_CLIENT_ID,
            'kid': 'my_key_id',
            'name': 'Anonymous user'
        }

        # Define the secret key to sign the JWT token
        secret_key = 'my_secret_key'
        # Create the JWT token
        headers = {'kid': secret_key}
        access_token = jwt.encode(payload_for_access_token, secret_key, algorithm='HS256', headers=headers)
        payload_for_id_token = payload_for_access_token
        groups = [f"{settings.CP_APP_NAME}-{settings.CP_AUTH_BYPASS_ENV}-{settings.ADMIN_ROLE_NAME}"]
        payload_for_id_token['groups'] = groups
        payload_for_id_token['email'] = "no-mail-id@invaliddomain.com"
        id_token = jwt.encode(payload_for_access_token, secret_key, algorithm='HS256', headers=headers)
        return IdAndAccessToken(access_token=access_token, id_token=id_token)

    def renew_token(self, **kwargs) -> IdAndAccessToken:
        pass
