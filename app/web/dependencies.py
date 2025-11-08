"""Helper dependencies for server-rendered views."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import ValidationError

from libkoiki.api.dependencies import DBSessionDep
from libkoiki.core.config import settings
from libkoiki.core.logging import get_logger
from libkoiki.models.user import UserModel
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.schemas.token import TokenPayload

logger = get_logger(__name__)


async def get_optional_active_user(
    request: Request,
    db: DBSessionDep,
) -> Optional[UserModel]:
    """Return the current user if a valid cookie token exists."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError) as exc:
        logger.debug("Failed to decode access token from cookie", error=str(exc))
        return None

    if not token_data.sub:
        return None

    user_repo = UserRepository()
    user_repo.set_session(db)
    user = await user_repo.get_user_with_roles_permissions(int(token_data.sub))

    if not user or not user.is_active:
        return None

    return user


async def require_active_user(
    current_user: Annotated[Optional[UserModel], Depends(get_optional_active_user)],
) -> UserModel:
    """Ensure the request is authenticated via cookie tokens."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


OptionalWebUser = Annotated[
    Optional[UserModel],
    Depends(get_optional_active_user),
]

WebActiveUser = Annotated[
    UserModel,
    Depends(require_active_user),
]
