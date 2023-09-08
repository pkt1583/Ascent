import logging
from abc import ABC, abstractmethod

from app.core.auth.user import User
from app.core.config import get_settings

settings = get_settings()

log = logging.getLogger(__name__)


class IdAndAccessToken:
    def __init__(self, access_token, id_token):
        self.access_token = access_token
        self.id_token = id_token


class TokenProvider(ABC):
    @abstractmethod
    def get_id_and_access_token(self, **kwargs) -> IdAndAccessToken:
        """Return raw access token"""

    @abstractmethod
    def renew_token(self, **kwargs) -> IdAndAccessToken:
        """This method is supposed to renew the token"""


class TokenService(ABC):
    @abstractmethod
    def get_token_provider(self) -> TokenProvider:
        "implement get token Provider"

    @abstractmethod
    def decode_and_check_authorization(self, expected_roles, **kwargs) -> User:
        "implement decode token and check auth"
