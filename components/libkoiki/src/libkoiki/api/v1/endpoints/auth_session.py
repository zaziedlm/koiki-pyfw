import structlog
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from libkoiki.api.dependencies import (
    ActiveUserDep,
    AuthServiceDep,
    DBSessionDep,
    LoginSecurityServiceDep,
    UserServiceDep,
)
from libkoiki.api.v1.endpoints.auth_basic import authenticate_password_and_create_token_pair
from libkoiki.core.auth_cookies import clear_auth_cookies, set_auth_cookies
from libkoiki.core.auth_decorators import handle_auth_errors
from libkoiki.core.config import settings
from libkoiki.core.csrf import issue_csrf_token, require_valid_csrf_token
from libkoiki.core.exceptions import AuthenticationException
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.security import extract_device_info
from libkoiki.core.security_logger import (
    SECURITY_EVENT_REFRESH_TOKEN_REJECTED,
    security_logger,
)
from libkoiki.schemas.auth import AuthResponse
from libkoiki.schemas.auth_session import (
    CSRFTokenResponse,
    SessionAuthResponse,
    SessionLoginRequest,
)
from libkoiki.schemas.user import UserCreate, UserResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/session", tags=["Authentication - Session"])


def _user_payload(user: object) -> dict:
    return UserResponse.model_validate(user).model_dump(mode="json")


@router.get("/csrf", response_model=CSRFTokenResponse)
async def get_session_csrf(response: Response) -> CSRFTokenResponse:
    token = issue_csrf_token(response)
    return CSRFTokenResponse(csrf_token=token, header_name=settings.AUTH_CSRF_HEADER_NAME)


@router.post("/login", response_model=SessionAuthResponse)
@limiter.limit("10/minute")
@handle_auth_errors("session_login")
async def session_login(
    request: Request,
    login_data: SessionLoginRequest,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    login_security_service: LoginSecurityServiceDep,
    db: DBSessionDep,
) -> JSONResponse:
    require_valid_csrf_token(request)

    user, access_token, refresh_token, _ = await authenticate_password_and_create_token_pair(
        request,
        email=login_data.login_identifier,
        password=login_data.password,
        user_service=user_service,
        auth_service=auth_service,
        login_security_service=login_security_service,
        db=db,
    )

    response = JSONResponse(
        {
            "message": "Login successful",
            "user": _user_payload(user),
            "location": "/dashboard",
        }
    )
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    issue_csrf_token(response)
    return response


@router.post(
    "/register",
    response_model=SessionAuthResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
@handle_auth_errors("session_registration")
async def session_register(
    request: Request,
    user_in: UserCreate,
    user_service: UserServiceDep,
    db: DBSessionDep,
) -> JSONResponse:
    require_valid_csrf_token(request)

    logger.info("Session user registration attempt")
    new_user = await user_service.create_user(user_in, db)

    response = JSONResponse(
        {
            "message": "User registered successfully",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "is_active": new_user.is_active,
                "created_at": new_user.created_at.isoformat(),
            },
            "location": "/auth/login",
        },
        status_code=status.HTTP_201_CREATED,
    )
    issue_csrf_token(response)
    return response


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("10/minute")
@handle_auth_errors("session_token_refresh")
async def session_refresh(
    request: Request,
    auth_service: AuthServiceDep,
    db: DBSessionDep,
) -> JSONResponse:
    require_valid_csrf_token(request)

    refresh_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if not refresh_token:
        response = JSONResponse(
            {"message": "Refresh token not found", "data": {"code": "REFRESH_TOKEN_MISSING"}},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        clear_auth_cookies(response)
        return response

    try:
        access_token, new_refresh_token, _ = await auth_service.refresh_access_token(
            refresh_token=refresh_token,
            db=db,
            device_info=extract_device_info(request),
            enable_rotation=True,
        )
    except AuthenticationException as exc:
        security_logger.log_security_event(
            SECURITY_EVENT_REFRESH_TOKEN_REJECTED,
            severity="warning",
            ip_address=request.client.host if request.client else None,
            user_agent=extract_device_info(request),
            endpoint="/auth/session/refresh",
            auth_method="refresh_token_cookie",
            failure_reason=exc.detail,
        )
        response = JSONResponse(
            {"message": exc.detail, "data": {"code": "REFRESH_TOKEN_INVALID"}},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        clear_auth_cookies(response)
        return response

    response = JSONResponse({"message": "Token refreshed"})
    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=new_refresh_token or refresh_token,
    )
    issue_csrf_token(response)
    return response


@router.post("/logout", response_model=AuthResponse)
@handle_auth_errors("session_logout")
async def session_logout(
    request: Request,
    auth_service: AuthServiceDep,
    db: DBSessionDep,
) -> JSONResponse:
    require_valid_csrf_token(request)

    refresh_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            await auth_service.revoke_refresh_token(refresh_token, db)
        except Exception:
            logger.warning("Failed to revoke session refresh token")

    response = JSONResponse({"message": "Logout successful"})
    clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserResponse)
async def session_me(current_user: ActiveUserDep) -> UserResponse:
    return UserResponse.model_validate(current_user)
