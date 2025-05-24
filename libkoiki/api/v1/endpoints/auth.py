# src/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
import structlog

from libkoiki.schemas.token import Token
from libkoiki.schemas.user import UserCreate, UserResponse
from libkoiki.core.dependencies import get_db
from libkoiki.services.user_service import UserService
from libkoiki.core.security import create_access_token
from libkoiki.core.exceptions import AuthenticationException, ValidationException
from libkoiki.core.rate_limiter import limiter  # 直接limiterを使用
from libkoiki.core.config import settings
from libkoiki.core.dependencies import UserServiceDep

logger = structlog.get_logger(__name__)

router = APIRouter()

# ログインエンドポイント（レートリミット付き）
@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # limiterを使用したレートリミット
async def login_for_access_token(
    request: Request, # limiterを使う場合は request が必要
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
) -> Token:
    """
    OAuth2互換のトークンエンドポイント。
    メールアドレスとパスワードで認証し、アクセストークンを返します。

    - **username**: ユーザーのメールアドレス
    - **password**: ユーザーのパスワード
    """
    logger.info("Login attempt", email=form_data.username)
    user = await user_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    if not user:
        logger.warning("Login failed: Incorrect email or password", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning("Login failed: Inactive user", email=form_data.username, user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    logger.info("Login successful", email=user.email, user_id=user.id)
    return Token(access_token=access_token, token_type="bearer")

# TODO: リフレッシュトークンエンドポイントも必要に応じて実装
# @router.post("/refresh", response_model=Token) ...

# TODO: パスワードリセット関連のエンドポイント
# @router.post("/password-recovery/{email}") ...
# @router.post("/reset-password/") ...