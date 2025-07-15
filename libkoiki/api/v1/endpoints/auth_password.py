# src/api/v1/endpoints/auth_password.py
from fastapi import APIRouter, HTTPException, status, Request
import structlog

from libkoiki.schemas.auth import (
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    AuthResponse
)
from libkoiki.api.dependencies import (
    DBSessionDep,
    UserServiceDep,
    ActiveUserDep,
    PasswordResetServiceDep
)
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.auth_decorators import handle_auth_errors
from libkoiki.core.security import extract_device_info

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/password-change", response_model=AuthResponse)
@limiter.limit("5/minute")
@handle_auth_errors("password_change")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: ActiveUserDep,
    user_service: UserServiceDep,
    db: DBSessionDep,
) -> AuthResponse:
    """
    認証済みユーザーのパスワード変更。
    
    - **current_password**: 現在のパスワード
    - **new_password**: 新しいパスワード（8文字以上、複雑性要件あり）
    """
    logger.info("Password change attempt", user_id=current_user.id)
    
    # 現在のパスワードを検証
    authenticated_user = await user_service.authenticate_user(
        current_user.email, password_data.current_password
    )
    if not authenticated_user:
        logger.warning("Password change failed - incorrect current password", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # パスワードを更新
    from libkoiki.schemas.user import UserUpdate
    update_data = UserUpdate(password=password_data.new_password)
    await user_service.update_user(current_user.id, update_data, db)
    
    logger.info("Password changed successfully", user_id=current_user.id)
    return AuthResponse(message="Password changed successfully")

@router.post("/password-reset/request", response_model=AuthResponse)
@limiter.limit("3/minute")
@handle_auth_errors("password_reset_request")
async def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    user_service: UserServiceDep,
    password_reset_service: PasswordResetServiceDep,
    db: DBSessionDep,
) -> AuthResponse:
    """
    パスワードリセット要求。
    
    指定されたメールアドレスが登録されている場合、パスワードリセット用のトークンを発行します。
    セキュリティ上の理由から、メールアドレスの存在有無に関わらず同じレスポンスを返します。
    
    注意: 現在はメール送信機能は未実装のため、ログにトークンを出力します。
    
    - **email**: パスワードリセット対象のメールアドレス
    """
    logger.info("Password reset request", email=reset_data.email)
    
    # ユーザーの存在確認
    user = await user_service.get_user_by_email(reset_data.email, db)
    
    if user and user.is_active:
        # デバイス情報を取得
        device_info = extract_device_info(request)
        ip_address = request.client.host if request.client else None
        
        # リセットトークンを生成
        reset_token, token_model = await password_reset_service.create_reset_token(
            user=user,
            db=db,
            ip_address=ip_address,
            user_agent=device_info
        )
        
        # 注意: 本格運用時にはメール配信サービスでトークンを送信
        # 開発環境では、ログにトークンを出力（実際の運用では削除）
        logger.info(
            "Password reset token generated (DEV ONLY - remove in production)", 
            user_id=user.id, 
            email=user.email,
            reset_token=reset_token,  # 本番では削除必須
            expires_at=token_model.expires_at.isoformat()
        )
    else:
        # ユーザーが存在しない場合もログに記録（但し、レスポンスは同じ）
        logger.info("Password reset requested for non-existent or inactive user", email=reset_data.email)
    
    # セキュリティ上、メールアドレスの存在有無に関わらず同じレスポンス
    return AuthResponse(message="Password reset email sent if account exists")

@router.post("/password-reset/confirm", response_model=AuthResponse)
@limiter.limit("5/minute")
@handle_auth_errors("password_reset_confirm")
async def confirm_password_reset(
    request: Request,
    reset_data: PasswordResetConfirm,
    user_service: UserServiceDep,
    password_reset_service: PasswordResetServiceDep,
    db: DBSessionDep,
) -> AuthResponse:
    """
    パスワードリセット確認・実行。
    
    リセットトークンを検証し、新しいパスワードに変更します。
    
    - **token**: パスワードリセットトークン
    - **new_password**: 新しいパスワード（8文字以上、複雑性要件あり）
    """
    logger.info("Password reset confirmation attempt", token=reset_data.token[:10] + "...")
    
    # リセットトークンを検証し、パスワードリセットを完了
    user = await password_reset_service.complete_password_reset(
        token=reset_data.token,
        new_password=reset_data.new_password,
        db=db
    )
    
    # パスワードを更新
    from libkoiki.schemas.user import UserUpdate
    update_data = UserUpdate(password=reset_data.new_password)
    await user_service.update_user(user.id, update_data, db)
    
    # 既存のリフレッシュトークンも無効化（セキュリティ強化）
    await password_reset_service.revoke_user_tokens(user.id, db)
    
    logger.info("Password reset completed successfully", user_id=user.id, email=user.email)
    return AuthResponse(
        message="Password reset completed successfully",
        data={"user_email": user.email}
    )