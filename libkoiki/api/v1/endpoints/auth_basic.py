# src/api/v1/endpoints/auth_basic.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
import structlog

from libkoiki.schemas.token import TokenWithRefresh
from libkoiki.schemas.user import UserCreate, UserResponse
from libkoiki.schemas.auth import AuthResponse
from libkoiki.api.dependencies import (
    DBSessionDep,
    UserServiceDep,
    ActiveUserDep,
    AuthServiceDep,
    LoginSecurityServiceDep
)
from libkoiki.core.security import extract_device_info
from libkoiki.core.exceptions import ValidationException
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.auth_decorators import handle_auth_errors

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/login", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
@handle_auth_errors("login")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    login_security_service: LoginSecurityServiceDep,
    db: DBSessionDep,
) -> TokenWithRefresh:
    """
    OAuth2互換のトークンエンドポイント。
    メールアドレスとパスワードで認証し、アクセストークンとリフレッシュトークンを返します。

    - **username**: ユーザーのメールアドレス
    - **password**: ユーザーのパスワード
    """
    email = form_data.username
    ip_address = request.client.host if request.client else "unknown"
    device_info = extract_device_info(request)
    
    logger.info("Login attempt", email=email, ip_address=ip_address)
    
    # ログイン試行制限チェック
    is_allowed, lockout_reason, retry_after = await login_security_service.check_login_allowed(
        email=email, ip_address=ip_address, db=db
    )
    
    if not is_allowed:
        logger.warning("Login blocked by security policy", email=email, ip_address=ip_address, reason=lockout_reason)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=lockout_reason,
            headers={"Retry-After": str(retry_after)} if retry_after else {}
        )
    
    # 段階的遅延を適用
    await login_security_service.apply_progressive_delay(email, ip_address, db)
    
    # 認証試行
    user = await user_service.authenticate_user(
        email=email, password=form_data.password
    )
    
    if not user:
        # 失敗ログイン試行を記録
        await login_security_service.record_login_attempt(
            email=email,
            ip_address=ip_address,
            is_successful=False,
            db=db,
            user_agent=device_info,
            failure_reason="invalid_credentials"
        )
        
        logger.warning("Login failed: Incorrect email or password", email=email, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # 失敗ログイン試行を記録
        await login_security_service.record_login_attempt(
            email=email,
            ip_address=ip_address,
            is_successful=False,
            db=db,
            user_id=user.id,
            user_agent=device_info,
            failure_reason="inactive_user"
        )
        
        logger.warning("Login failed: Inactive user", email=email, user_id=user.id, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # 成功ログイン試行を記録
    await login_security_service.record_login_attempt(
        email=email,
        ip_address=ip_address,
        is_successful=True,
        db=db,
        user_id=user.id,
        user_agent=device_info
    )

    # トークンペアの生成
    access_token, refresh_token, expires_in = await auth_service.create_token_pair(
        user=user, db=db, device_info=device_info
    )
    
    logger.info("Login successful", email=user.email, user_id=user.id, ip_address=ip_address)
    return TokenWithRefresh(
        access_token=access_token, 
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
@handle_auth_errors("registration")
async def register(
    request: Request,
    user_in: UserCreate,
    user_service: UserServiceDep,
    db: DBSessionDep,
) -> AuthResponse:
    """
    新規ユーザー登録。
    
    - **email**: ユーザーのメールアドレス（一意）
    - **password**: パスワード（8文字以上、複雑性要件あり）
    - **full_name**: ユーザーの氏名（任意）
    """
    logger.info("User registration attempt", email=user_in.email)
    
    new_user = await user_service.create_user(user_in, db)
    logger.info("User registered successfully", user_id=new_user.id, email=new_user.email)
    
    # レスポンス用のユーザー情報を準備
    user_info = {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat()
    }
    
    return AuthResponse(
        message="User registered successfully",
        user=user_info
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: ActiveUserDep,
) -> UserResponse:
    """
    現在認証されているユーザーの情報を取得。
    
    認証が必要（Bearer token）。
    """
    logger.debug("Getting current user info", user_id=current_user.id)
    return UserResponse.model_validate(current_user)

@router.post("/logout", response_model=AuthResponse)
async def logout(
    current_user: ActiveUserDep,
) -> AuthResponse:
    """
    ログアウト。
    
    注意: JWTトークンはステートレスなため、クライアント側でトークンを破棄する必要があります。
    このエンドポイントは主にログアウト処理の統一化とログ記録のために提供されます。
    """
    logger.info("User logout", user_id=current_user.id, email=current_user.email)
    return AuthResponse(message="Successfully logged out")