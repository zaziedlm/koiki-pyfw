"""Cookie-backed browser API used by the standalone React frontend.

This router is intentionally separate from the existing OAuth2/Bearer endpoints.
It provides an explicit BFF-like boundary inside FastAPI: tokens are written to
HttpOnly cookies and response bodies never expose access or refresh tokens.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, model_validator

from libkoiki.api.dependencies import (
    AuthServiceDep,
    DBSessionDep,
    LoginSecurityServiceDep,
    TodoServiceDep,
    UserServiceDep,
)
from libkoiki.api.v1.endpoints import auth_basic, auth_token, todos
from libkoiki.core.browser_session import (
    BrowserActiveUserDep,
    clear_auth_cookies,
    require_browser_csrf,
    set_auth_cookies,
    set_csrf_cookie,
)
from libkoiki.core.config import settings
from libkoiki.schemas.browser_session import BrowserSessionResponse
from libkoiki.schemas.refresh_token import RefreshTokenRequest
from libkoiki.schemas.todo import TodoCreate, TodoResponse, TodoUpdate
from libkoiki.schemas.user import UserResponse

router = APIRouter(prefix="/browser")


class BrowserLoginRequest(BaseModel):
    """Password-login payload accepted from the browser session boundary."""

    email: str | None = None
    username: str | None = None
    password: str

    @model_validator(mode="after")
    def require_login_name(self) -> "BrowserLoginRequest":
        if not (self.email or self.username):
            raise ValueError("email or username is required")
        return self


class _LoginForm:
    """Small adapter for the existing OAuth2 password login implementation."""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password


@router.get("/csrf")
async def issue_csrf_token(response: Response) -> dict[str, str]:
    """Issue/rotate the non-HttpOnly half of the double-submit CSRF token."""
    return {"csrf_token": set_csrf_cookie(response)}


@router.post("/login", response_model=BrowserSessionResponse)
async def browser_login(
    request: Request,
    response: Response,
    payload: BrowserLoginRequest,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    login_security_service: LoginSecurityServiceDep,
    db: DBSessionDep,
) -> BrowserSessionResponse:
    require_browser_csrf(request)

    token_pair = await auth_basic.login_for_access_token(
        request=request,
        form_data=_LoginForm(payload.email or payload.username or "", payload.password),
        user_service=user_service,
        auth_service=auth_service,
        login_security_service=login_security_service,
        db=db,
    )
    set_auth_cookies(
        response,
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )
    set_csrf_cookie(response)
    return BrowserSessionResponse(message="Login successful", expires_in=token_pair.expires_in)


@router.post("/refresh", response_model=BrowserSessionResponse)
async def browser_refresh(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
    db: DBSessionDep,
) -> BrowserSessionResponse:
    require_browser_csrf(request)
    refresh_token = request.cookies.get(settings.BROWSER_REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing")

    token_pair = await auth_token.refresh_token(
        request=request,
        refresh_data=RefreshTokenRequest(refresh_token=refresh_token),
        auth_service=auth_service,
        db=db,
    )
    set_auth_cookies(
        response,
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )
    set_csrf_cookie(response)
    return BrowserSessionResponse(message="Session refreshed", expires_in=token_pair.expires_in)


@router.post("/logout", response_model=BrowserSessionResponse)
async def browser_logout(
    request: Request,
    response: Response,
    current_user: BrowserActiveUserDep,
) -> BrowserSessionResponse:
    require_browser_csrf(request)
    await auth_basic.logout(current_user=current_user)
    clear_auth_cookies(response)
    set_csrf_cookie(response)
    return BrowserSessionResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def browser_me(current_user: BrowserActiveUserDep) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/todos", response_model=list[TodoResponse])
async def browser_read_todos(
    request: Request,
    current_user: BrowserActiveUserDep,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    skip: int = 0,
    limit: int = 100,
):
    return await todos.read_todos(
        request=request,
        current_user=current_user,
        todo_service=todo_service,
        db=db,
        skip=skip,
        limit=limit,
    )


@router.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def browser_create_todo(
    request: Request,
    todo_in: TodoCreate,
    current_user: BrowserActiveUserDep,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
):
    require_browser_csrf(request)
    return await todos.create_todo(
        request=request,
        todo_in=todo_in,
        current_user=current_user,
        todo_service=todo_service,
        db=db,
    )


@router.put("/todos/{todo_id}", response_model=TodoResponse)
async def browser_update_todo(
    request: Request,
    todo_id: int,
    todo_in: TodoUpdate,
    current_user: BrowserActiveUserDep,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
):
    require_browser_csrf(request)
    return await todos.update_todo(
        request=request,
        todo_id=todo_id,
        todo_in=todo_in,
        current_user=current_user,
        todo_service=todo_service,
        db=db,
    )


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def browser_delete_todo(
    request: Request,
    todo_id: int,
    current_user: BrowserActiveUserDep,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
) -> None:
    require_browser_csrf(request)
    await todos.delete_todo(
        request=request,
        todo_id=todo_id,
        current_user=current_user,
        todo_service=todo_service,
        db=db,
    )
