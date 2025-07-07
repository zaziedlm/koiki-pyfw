# src/api/v1/endpoints/auth_token.py
from fastapi import APIRouter, Request
import structlog

from libkoiki.schemas.token import TokenWithRefresh
from libkoiki.schemas.refresh_token import RefreshTokenRequest
from libkoiki.schemas.auth import AuthResponse
from libkoiki.api.dependencies import (
    DBSessionDep,
    ActiveUserDep,
    AuthServiceDep
)
from libkoiki.core.security import extract_device_info
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.auth_decorators import handle_auth_errors

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/refresh", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
@handle_auth_errors("token_refresh")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    auth_service: AuthServiceDep,
    db: DBSessionDep,
) -> TokenWithRefresh:
    """
    リフレッシュトークンを使って新しいアクセストークンを取得します。
    
    - **refresh_token**: リフレッシュトークン
    """
    logger.info("Token refresh attempt")
    
    # デバイス情報の抽出
    device_info = extract_device_info(request)
    
    # アクセストークンをリフレッシュ（トークンローテーション有効）
    access_token, new_refresh_token, expires_in = await auth_service.refresh_access_token(
        refresh_token=refresh_data.refresh_token,
        db=db,
        device_info=device_info,
        enable_rotation=True
    )
    
    logger.info("Token refresh successful")
    
    return TokenWithRefresh(
        access_token=access_token,
        refresh_token=new_refresh_token or refresh_data.refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )

@router.post("/revoke-all-tokens", response_model=AuthResponse)
@handle_auth_errors("revoke_all_tokens")
async def revoke_all_tokens(
    current_user: ActiveUserDep,
    auth_service: AuthServiceDep,
    db: DBSessionDep,
) -> AuthResponse:
    """
    現在のユーザーのすべてのリフレッシュトークンを無効化します。
    
    これにより、すべてのデバイスからログアウトされます。
    """
    logger.info("Revoking all tokens for user", user_id=current_user.id)
    
    revoked_count = await auth_service.revoke_user_tokens(
        user_id=current_user.id,
        db=db,
        exclude_current=False  # 現在のトークンも含めて全て無効化
    )
    
    logger.info("All tokens revoked", user_id=current_user.id, count=revoked_count)
    return AuthResponse(
        message=f"Successfully revoked {revoked_count} refresh tokens",
        data={"revoked_count": revoked_count}
    )