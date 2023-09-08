import logging
from typing import Optional

from fastapi import HTTPException, Request
from starlette import status

from app.core.auth.exception import IdTokenMissingException, AccessTokenMissingException, UnAuthorizedException
from app.core.auth.token_service import get_token_service
from app.core.auth.user import User
from app.core.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


class ValidateAndReturnUser:
    def __init__(self, expected_roles: list[str]) -> None:
        self.expected_roles = expected_roles or []

    async def __call__(self, request: Request) -> Optional[User]:

        user = User(id_token="Some dummy id token that won't be used", name="Dummy",
                    access_token="some dummy access token", role_collection=None,
                    claims={"email": "no-mail-id@invaliddomain.com"})
        try:
            user = await get_token_service().decode_and_check_authorization(self.expected_roles, request=request)
        except (IdTokenMissingException, AccessTokenMissingException) as exp:
            log.error(exp)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated",
                                headers={"WWW-Authenticate": "Bearer"})
        except UnAuthorizedException as exp:
            log.error(exp)
            raise HTTPException(status_code=403,
                                detail=f"Not authorized. You need to be a member of the {self.expected_roles} roles. "
                                       f"Your "
                                       f"current roles are {user.role_collection}")
        return user
