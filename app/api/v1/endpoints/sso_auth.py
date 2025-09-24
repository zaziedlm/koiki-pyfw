# app/api/v1/endpoints/sso_auth.py
"""
SSO認証APIエンドポイント

OpenID Connect による外部認証サービスとの連携エンドポイントを提供
IDトークンを受け取り、内部認証トークンを返す
"""

from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, status

from app.core.sso_config import SSOSettings, get_sso_settings
from app.schemas.sso import SSOLinkResponse, SSOLoginRequest, SSOUserInfoResponse
from app.services.sso_service import SSOService
from libkoiki.api.dependencies import (
    AuthServiceDep,
    DBSessionDep,
    UserServiceDep,
)
from libkoiki.core.auth_decorators import handle_auth_errors
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.security import extract_device_info
from libkoiki.core.security_logger import security_logger
from libkoiki.core.security_metrics import security_metrics
from libkoiki.schemas.token import TokenWithRefresh

logger = structlog.get_logger(__name__)

router = APIRouter()


# 依存性注入用のファクトリ関数
def get_sso_service(
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    sso_settings: Annotated[SSOSettings, Depends(get_sso_settings)],
) -> SSOService:
    """
    SSOService インスタンスを取得

    依存性注入システムでSSOServiceを提供
    """
    return SSOService(
        user_service=user_service, auth_service=auth_service, sso_settings=sso_settings
    )


SSOServiceDep = Annotated[SSOService, Depends(get_sso_service)]




async def parse_sso_login_request(
    sso_json: Optional[SSOLoginRequest] = Body(default=None),
    access_token_form: Optional[str] = Form(default=None, description="OAuth2 アクセストークン"),
) -> SSOLoginRequest:
    if sso_json and sso_json.access_token:
        return sso_json
    if access_token_form:
        return SSOLoginRequest(access_token=access_token_form)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="access_token is required",
    )

@router.post("/sso/login", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
@handle_auth_errors("sso_login")
async def sso_login(
    request: Request,
    sso_request: Annotated[SSOLoginRequest, Depends(parse_sso_login_request)],
    sso_service: SSOServiceDep,
    db: DBSessionDep,
) -> TokenWithRefresh:
    """
    SSO ログインエンドポイント

    BFF が ID トークンの検証を担い、本 API は IdP から払い出された OAuth2 アクセストークンのみを受け取り内部トークンへ交換する。

    処理フロー:
    1. アクセストークンを検証する（JWKS 検証またはイントロスペクション）。
    2. SSO ユーザーをローカルユーザーと連携・必要に応じて自動作成する。
    3. KOIKI 内部で利用するアクセストークン／リフレッシュトークンを発行する。

    Args:
        sso_request: 上流から受け取ったアクセストークンを含む SSO ログインリクエスト。

    Returns:
        内部アクセストークンとリフレッシュトークンのペア。

    Raises:
        HTTPException: 認証失敗やトークン交換に失敗した場合。
    """
    ip_address = request.client.host if request.client else "unknown"
    device_info = extract_device_info(request)

    logger.info("SSO login attempt", ip_address=ip_address, device_info=device_info)

    try:
        # 1. Validate the access token and extract subject claims
        user_info = await sso_service.verify_access_token(sso_request.access_token)

        logger.info(
            "Access token verification successful",
            email=user_info.email,
            sub=user_info.sub,
            ip_address=ip_address,
        )

        # 2. Authenticate the SSO user against the local store
        user, sso_response = await sso_service.authenticate_sso_user(user_info, db)

        logger.info(
            "SSO user authentication successful",
            user_id=user.id,
            email=user.email,
            is_new_user=sso_response.is_new_user,
            ip_address=ip_address,
        )

        # 3. Issue the internal token pair used by KOIKI services
        (
            access_token,
            refresh_token,
            expires_in,
        ) = await sso_service.create_internal_token_pair(
            user=user, db=db, device_info=device_info
        )

        # セキュリティログとメトリクスに成功を記録
        security_logger.log_authentication_attempt(
            email=user.email,
            ip_address=ip_address,
            user_agent=device_info,
            success=True,
            user_id=user.id,
        )
        security_metrics.record_authentication_attempt(
            success=True, email=user.email, ip_address=ip_address
        )

        logger.info(
            "SSO login successful",
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
        )

        return TokenWithRefresh(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    except HTTPException as e:
        # セキュリティログに失敗を記録
        security_logger.log_authentication_attempt(
            email=getattr(locals().get("user_info"), "email", "unknown"),
            ip_address=ip_address,
            user_agent=device_info,
            success=False,
            failure_reason="sso_verification_failed",
        )
        security_metrics.record_authentication_attempt(
            success=False,
            email=getattr(locals().get("user_info"), "email", "unknown"),
            ip_address=ip_address,
            failure_reason="sso_verification_failed",
        )

        logger.warning(
            "SSO login failed",
            error=e.detail,
            status_code=e.status_code,
            ip_address=ip_address,
        )
        raise

    except Exception as e:
        # 予期しないエラー
        security_logger.log_authentication_attempt(
            email="unknown",
            ip_address=ip_address,
            user_agent=device_info,
            success=False,
            failure_reason="internal_error",
        )
        security_metrics.record_authentication_attempt(
            success=False,
            email="unknown",
            ip_address=ip_address,
            failure_reason="internal_error",
        )

        logger.error(
            "Unexpected error during SSO login", error=str(e), ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO login failed due to internal error",
        )


@router.get("/sso/user-info", response_model=SSOUserInfoResponse)
@limiter.limit("30/minute")
async def get_sso_user_info(
    request: Request,
    user_service: UserServiceDep,
    db: DBSessionDep,
    # 認証が必要な場合は ActiveUserDep を追加
) -> SSOUserInfoResponse:
    """
    SSO連携ユーザー情報取得エンドポイント

    現在認証されているユーザーのSSO連携情報を取得します。
    管理画面やプロファイル画面での表示用途。

    Returns:
        SSO連携ユーザー情報
    """
    # TODO: 認証機能実装後に ActiveUserDep を追加し、current_user を取得
    # current_user: ActiveUserDep の形で依存性注入

    logger.info("SSO user info request")

    # 暫定実装：実際の実装では認証されたユーザーのSSO情報を返す
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="SSO user info endpoint not yet implemented",
    )


@router.get("/sso/health")
@limiter.limit("60/minute")
async def sso_health_check(
    request: Request, sso_settings: Annotated[SSOSettings, Depends(get_sso_settings)]
) -> dict:
    """
    SSO 機能ヘルスチェック

    SSO設定の妥当性と外部サービスへの接続性をチェック

    Returns:
        ヘルスチェック結果
    """
    logger.info("SSO health check requested")

    health_status = {
        "sso_enabled": True,
        "settings_valid": sso_settings.validate_required_settings(),
        "jwks_uri_configured": bool(sso_settings.SSO_JWKS_URI),
        "auto_create_users": sso_settings.SSO_AUTO_CREATE_USERS,
        "signature_validation": sso_settings.SSO_SIGNATURE_VALIDATION,
    }

    # JWKS接続テスト（オプション）
    jwks_accessible = False
    if sso_settings.SSO_JWKS_URI:
        try:
            try:
                import httpx  # 遅延インポート
            except Exception:
                httpx = None  # type: ignore

            if httpx is not None:
                verify_ssl = not sso_settings.SSO_SKIP_SSL_VERIFY
                timeout = httpx.Timeout(3.0, connect=2.0)
                # HEAD が許可されていない場合に備えて GET にフォールバック
                async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
                    resp = await client.request("HEAD", sso_settings.SSO_JWKS_URI)
                    if resp.status_code >= 400:
                        resp = await client.get(sso_settings.SSO_JWKS_URI)
                    jwks_accessible = resp.status_code < 400
            else:
                logger.warning("httpx not available; skipping JWKS reachability test")
        except Exception as e:
            logger.warning("JWKS endpoint health check failed", error=str(e))
            jwks_accessible = False

    health_status["jwks_accessible"] = jwks_accessible
    health_status["overall_status"] = (
        "healthy"
        if all([health_status["settings_valid"], health_status["jwks_uri_configured"]])
        else "degraded"
    )

    logger.info("SSO health check completed", status=health_status["overall_status"])

    return health_status
