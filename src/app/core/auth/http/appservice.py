from typing import List

from fastapi import HTTPException
from starlette.requests import Request

from app.core.auth.token import IdAndAccessToken, TokenProvider
from app.utils import retryable_requester
from app.utils.constants import APP_SERVICE_ACCESS_TOKEN_HEADER, APP_SERVICE_ID_TOKEN_HEADER


class AppServiceBasedTokenProvider(TokenProvider):

    def get_id_and_access_token(self, **kwargs) -> IdAndAccessToken:
        """
        Get id and access token from request
        Args:
            **kwargs: request headers (access_token, id_token)
        Returns:
            IdAndAccessToken: id and access token
        """
        if kwargs['request'] is None:
            raise ValueError("Request is required argument")
        access_token = kwargs['request'].headers.get(APP_SERVICE_ACCESS_TOKEN_HEADER)
        id_token = kwargs['request'].headers.get(APP_SERVICE_ID_TOKEN_HEADER)
        return IdAndAccessToken(access_token=access_token, id_token=id_token)

    def renew_token(self, **kwargs) -> List[dict]:
        """
        Renew token
        Args:
            **kwargs: request
        Returns:
            List[dict]: new token
        """
        if kwargs['request'] is None:
            raise ValueError("Request is required argument")
        return self.__get_new_token(kwargs['request'])

    def __get_new_token(self, request: Request) -> List[dict]:
        """
        Get new token
        Args:
            request: request
        Returns:
            List[dict]: new token
        Exceptions:
            HTTPException: 403 if not authorized
        """
        self.__refresh_token(request)
        s = retryable_requester()
        new_token = s.get(f"{request.base_url}.auth/me", timeout=5, cookies=request.cookies)
        if new_token.status_code == 200:
            return new_token.json()
        raise HTTPException(status_code=403, detail="Not authorized.")

    @staticmethod
    def __refresh_token(request: Request) -> None:
        """
        Refresh token
        Args:
            request: request
        Exceptions:
            HTTPException: 403 if not authorized
        """
        s = retryable_requester()
        esp = s.get(f"{request.base_url}.auth/refresh", timeout=5, cookies=request.cookies, headers=request.headers)
        if esp.status_code == 200:
            return
        raise HTTPException(status_code=403, detail="Not authorized. Please refresh the page to re-initiate login.")
