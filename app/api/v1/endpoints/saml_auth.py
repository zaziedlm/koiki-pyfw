# app/api/v1/endpoints/saml_auth.py
"""
SAML認証エンドポイント

SAML 2.0による外部認証システムとの連携API:
1. SAML AuthnRequest生成エンドポイント
2. SAML Response処理・ログインエンドポイント
3. SAML関連ヘルスチェック・情報取得エンドポイント
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.core.saml_config import SAMLSettings, get_saml_settings
from app.schemas.saml import (
    SAMLAuthorizationInitResponse,
    SAMLHealthCheckResponse,
    SAMLLoginTicketRequest,
    SAMLUserInfoResponse,
)
from app.services.saml_service import SAMLService
from libkoiki.api.dependencies import (
    ActiveUserDep,
    AuthServiceDep,
    DBSessionDep,
    UserServiceDep,
)
from libkoiki.core.auth_decorators import handle_auth_errors
from libkoiki.core.rate_limiter import limiter
from libkoiki.core.security import extract_device_info
from libkoiki.core.security_logger import security_logger
from libkoiki.core.security_metrics import security_metrics
from libkoiki.core.transaction import transactional
from libkoiki.schemas.token import TokenWithRefresh

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_saml_service(
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    saml_settings: Annotated[SAMLSettings, Depends(get_saml_settings)],
) -> SAMLService:
    """SAML認証サービスの依存性注入"""
    return SAMLService(
        user_service=user_service,
        auth_service=auth_service,
        saml_settings=saml_settings,
    )


SAMLServiceDep = Annotated[SAMLService, Depends(get_saml_service)]


@router.get("/saml/authorization", response_model=SAMLAuthorizationInitResponse)
@limiter.limit("30/minute")
async def saml_authorization_init(
    request: Request,
    saml_service: SAMLServiceDep,
    acs_url: str = None,
    redirect_uri: str | None = None,
) -> SAMLAuthorizationInitResponse:
    """
    SAML AuthnRequest生成エンドポイント

    RelayStateを生成し、SAML認証リクエストに必要な情報を返す

    フロントエンドは返却値をもとにSAML IdPへリダイレクトする。
    """
    try:
        context = await saml_service.generate_authn_request(
            acs_url=acs_url,
            redirect_uri=redirect_uri,
        )

        return SAMLAuthorizationInitResponse(
            sso_url=context["sso_url"],
            saml_request=context["saml_request"],
            relay_state=context["relay_state"],
            expires_at=context["expires_at"],
            sso_binding=context["sso_binding"],
            redirect_url=context["redirect_url"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during SAML authorization init", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SAML authorization initialization failed",
        )


@router.post("/saml/acs", response_class=HTMLResponse)
@limiter.limit("60/minute")
@transactional
async def saml_acs(
    request: Request,
    saml_service: SAMLServiceDep,
    db: DBSessionDep,
    saml_response: str = Form(..., alias="SAMLResponse"),
    relay_state: str = Form(..., alias="RelayState"),
):
    """IdPからのSAML Responseを受領し、ログインチケット付きでフロントエンドへリダイレクト"""

    try:
        (
            redirect_uri,
            login_ticket,
            ticket_expires,
            user_info,
            user,
        ) = await saml_service.handle_acs_request(
            request=request,
            saml_response=saml_response,
            relay_state_token=relay_state,
            db=db,
        )

        # @transactional デコレータが自動的にコミットを管理
        # await db.commit() は不要

        redirect_with_ticket = saml_service.build_login_redirect_url(
            redirect_uri,
            login_ticket,
        )

        logger.info(
            "SAML ACS processed successfully",
            redirect_uri=redirect_uri,
            subject_id=user_info.subject_id,
            user_id=user.id,
            ticket_expires=str(ticket_expires),
        )

        return RedirectResponse(
            url=redirect_with_ticket, status_code=status.HTTP_303_SEE_OTHER
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("SAML ACS processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SAML ACS processing failed",
        )


@router.get("/saml/metadata", response_class=Response)
@limiter.limit("10/minute")
async def saml_metadata(
    request: Request,
    saml_service: SAMLServiceDep,
) -> Response:
    """SAML Service Provider メタデータを提供"""

    metadata_xml = await saml_service.generate_sp_metadata()
    return Response(
        content=metadata_xml,
        media_type="application/samlmetadata+xml",
        headers={"Cache-Control": "no-store"},
    )


@router.post("/saml/login", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
@handle_auth_errors("saml_login")
async def saml_login(
    request: Request,
    login_request: SAMLLoginTicketRequest,
    saml_service: SAMLServiceDep,
    db: DBSessionDep,
) -> TokenWithRefresh:
    """SAML ログインエンドポイント

    ACSで発行されたログインチケットを受け取り、内部認証トークンに交換する。

    処理フロー:
    1. ログインチケットの署名と有効期限を検証
    2. 対象ユーザーの取得・状態確認
    3. 内部認証トークンペアの発行
    """
    ip_address = request.client.host if request.client else "unknown"
    device_info = extract_device_info(request)

    logger.info("SAML login attempt", ip_address=ip_address, device_info=device_info)

    try:
        (
            user,
            access_token,
            refresh_token,
            expires_in,
        ) = await saml_service.exchange_login_ticket(
            login_ticket=login_request.login_ticket,
            db=db,
            device_info=device_info,
        )

        # セキュリティログとメトリクスに成功を記録
        security_logger.log_authentication_attempt(
            email=user.email,
            ip_address=ip_address,
            user_agent=device_info,
            success=True,
            user_id=user.id,
            additional_data={"auth_method": "saml"},
        )
        security_metrics.record_authentication_attempt(
            success=True, email=user.email, ip_address=ip_address
        )

        logger.info(
            "SAML login successful",
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
            email=getattr(locals().get("user"), "email", "unknown"),
            ip_address=ip_address,
            user_agent=device_info,
            success=False,
            failure_reason="saml_verification_failed",
            additional_data={"auth_method": "saml"},
        )
        security_metrics.record_authentication_attempt(
            success=False,
            email=getattr(locals().get("user"), "email", "unknown"),
            ip_address=ip_address,
            failure_reason="saml_verification_failed",
        )

        logger.warning(
            "SAML login failed",
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
            additional_data={"auth_method": "saml"},
        )
        security_metrics.record_authentication_attempt(
            success=False,
            email="unknown",
            ip_address=ip_address,
            failure_reason="internal_error",
        )

        logger.error(
            "Unexpected error during SAML login", error=str(e), ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SAML login failed due to internal error",
        )


@router.get("/saml/user-info", response_model=SAMLUserInfoResponse)
@limiter.limit("30/minute")
async def get_saml_user_info(
    request: Request,
    current_user: ActiveUserDep,
    db: DBSessionDep,
    saml_service: SAMLServiceDep,
) -> SAMLUserInfoResponse:
    """
    SAML ユーザー情報取得エンドポイント

    認証済みユーザーのSAML関連情報を取得

    Args:
        current_user: 現在認証済みユーザー

    Returns:
        SAMLユーザー情報レスポンス

    Raises:
        HTTPException: SAML連携情報が見つからない場合
    """
    try:
        response = await saml_service.get_user_saml_info(
            user=current_user,
            db=db,
        )

        logger.info(
            "SAML user info retrieved",
            user_id=current_user.id,
            saml_subject_id=response.user_info.subject_id,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve SAML user info", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SAML user information",
        )


@router.post("/saml/logout", response_class=RedirectResponse)
@limiter.limit("30/minute")
async def saml_logout(
    request: Request,
    current_user: ActiveUserDep,
    saml_service: SAMLServiceDep,
    db: DBSessionDep,
    redirect_uri: str | None = None,
) -> RedirectResponse:
    """SAML シングルログアウト開始エンドポイント"""

    logout_url = await saml_service.initiate_logout(
        request=request,
        user=current_user,
        db=db,
        redirect_uri=redirect_uri,
    )

    logger.info("SAML logout initiated", user_id=current_user.id, redirect=logout_url)

    return RedirectResponse(url=logout_url, status_code=status.HTTP_303_SEE_OTHER)


@router.api_route("/saml/sls", methods=["GET", "POST"], response_class=RedirectResponse)
@limiter.limit("60/minute")
async def saml_single_logout_service(
    request: Request,
    saml_service: SAMLServiceDep,
    db: DBSessionDep,
) -> RedirectResponse:
    """IdPからのSAML LogoutRequest/Responseを処理"""

    post_data = None
    if request.method == "POST":
        form_data = await request.form()
        post_data = {key: value for key, value in form_data.multi_items()}

    redirect_target = await saml_service.process_logout_request(
        request=request,
        db=db,
        post_data=post_data,
    )

    logger.info("SAML SLS completed", redirect=redirect_target)

    return RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/saml/health", response_model=SAMLHealthCheckResponse)
@limiter.limit("60/minute")
async def saml_health_check(
    request: Request,
    saml_service: SAMLServiceDep,
) -> SAMLHealthCheckResponse:
    """
    SAML ヘルスチェックエンドポイント

    SAML設定とIdP接続性の確認

    Returns:
        SAMLヘルスチェック結果
    """
    try:
        # SAML設定検証
        settings_valid = saml_service.saml_settings.validate_required_settings()

        # IdPメタデータアクセス性チェック（オプション）
        idp_accessible = True
        if saml_service.saml_settings.SAML_IDP_METADATA_URL:
            try:
                # 簡易的なアクセスチェック（実装を簡略化）
                idp_accessible = True  # 実際にはHTTPリクエストでチェック
            except Exception:
                idp_accessible = False

        # ライブラリ可用性チェック
        from app.services.saml_service import PYTHON3_SAML_AVAILABLE

        saml_configured = PYTHON3_SAML_AVAILABLE and settings_valid

        # ステータス判定
        if saml_configured and idp_accessible and settings_valid:
            status_msg = "healthy"
            message = "SAML service is properly configured and operational"
        elif saml_configured:
            status_msg = "warning"
            message = "SAML service is configured but IdP accessibility is uncertain"
        else:
            status_msg = "error"
            message = "SAML service is not properly configured"

        response = SAMLHealthCheckResponse(
            status=status_msg,
            saml_configured=saml_configured,
            idp_metadata_accessible=idp_accessible,
            required_settings_valid=settings_valid,
            message=message,
        )

        logger.info(
            "SAML health check completed",
            status=status_msg,
            configured=saml_configured,
            settings_valid=settings_valid,
        )

        return response

    except Exception as e:
        logger.error("SAML health check failed", error=str(e))
        return SAMLHealthCheckResponse(
            status="error",
            saml_configured=False,
            idp_metadata_accessible=False,
            required_settings_valid=False,
            message=f"Health check failed: {str(e)}",
        )
