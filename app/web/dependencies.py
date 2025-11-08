"""Helper dependencies for server-rendered views."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import ValidationError

from libkoiki.api.dependencies import DBSessionDep
from libkoiki.core.config import settings
from libkoiki.core.csrf import create_csrf_token, validate_csrf_token
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


def issue_csrf_token_for_user(user: Optional[UserModel]) -> Optional[str]:
    """Return a stateless CSRF token tied to the given user."""
    if not user:
        return None
    return create_csrf_token(
        subject=str(user.id),
        secret=settings.CSRF_SECRET,
        ttl_seconds=settings.CSRF_TOKEN_TTL_SECONDS,
    )


async def verify_web_csrf_token(
    current_user: WebActiveUser,
    csrf_header: Annotated[Optional[str], Header(alias="X-CSRF-Token")] = None,
) -> None:
    """Validate the CSRF token sent from HTMX requests."""
    if not csrf_header or not validate_csrf_token(
        token=csrf_header,
        subject=str(current_user.id),
        secret=settings.CSRF_SECRET,
        ttl_seconds=settings.CSRF_TOKEN_TTL_SECONDS,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
