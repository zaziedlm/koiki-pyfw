# app/services/saml_service.py
"""SAML認証サービス"""

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import structlog
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

# 条件付きインポート - 開発依存関係
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings

    PYTHON3_SAML_AVAILABLE = True
except ImportError:
    PYTHON3_SAML_AVAILABLE = False

from app.core.saml_config import SAMLSettings, get_saml_settings
from app.repositories.user_sso_repository import UserSSORepository
from app.schemas.saml import SAMLLinkResponse, SAMLUserInfo, SAMLUserInfoResponse
from app.services.saml_certificate_manager import SAMLCertificateManager
from libkoiki.core.security import check_password_complexity
from libkoiki.models.user import UserModel
from libkoiki.schemas.user import UserCreate
from libkoiki.services.auth_service import AuthService
from libkoiki.services.user_service import UserService

logger = structlog.get_logger(__name__)


_LOGIN_TICKET_CACHE: Dict[str, datetime] = {}
_LOGIN_TICKET_LOCK = asyncio.Lock()


class ValidationException(Exception):
    """SAML検証エラー専用例外"""

    pass


class SAMLService:
    """
    SAML認証サービスクラス

    SAML 2.0による外部認証との連携を処理:
    1. SAML AuthnRequest生成
    2. SAML Response署名検証
    3. 属性抽出・検証
    4. ローカルユーザーとの連携
    5. 内部認証トークンの発行
    """

    def __init__(
        self,
        user_service: UserService,
        auth_service: AuthService,
        saml_settings: SAMLSettings = None,
    ):
        self.user_service = user_service
        self.auth_service = auth_service
        self.saml_settings = saml_settings or get_saml_settings()
        self.user_sso_repository = UserSSORepository()

        if not PYTHON3_SAML_AVAILABLE:
            logger.warning(
                "python3-saml not available; SAML functionality will be limited"
            )

        if not self.saml_settings.SAML_RELAY_STATE_SIGNING_KEY:
            logger.error("RelayState signing key is not configured for SAML flow")
            raise RuntimeError("SAML RelayState signing key is required")

        self.relay_state_signing_key = (
            self.saml_settings.SAML_RELAY_STATE_SIGNING_KEY.encode("utf-8")
        )
        self.relay_state_ttl = timedelta(
            seconds=self.saml_settings.SAML_RELAY_STATE_TTL_SECONDS
        )
        self.login_ticket_ttl = timedelta(
            seconds=self.saml_settings.SAML_LOGIN_TICKET_TTL_SECONDS
        )

        # 証明書マネージャーの初期化（動的メタデータ取得/静的証明書に対応）
        self.cert_manager = SAMLCertificateManager(self.saml_settings)

        logger.info(
            "SAMLService initialized",
            cert_strategy=self.cert_manager.strategy,
            metadata_enabled=bool(self.saml_settings.SAML_IDP_METADATA_URL),
        )

    async def generate_authn_request(
        self,
        *,
        redirect_uri: Optional[str] = None,
        acs_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """AuthnRequestとRelayStateを生成し、IdPへリダイレクトするための情報を返す"""

        if not PYTHON3_SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="python3-saml is not available for SAML authentication",
            )

        if not self.saml_settings.validate_required_settings():
            logger.error("SAML settings validation failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML configuration is incomplete",
            )

        chosen_acs_url = acs_url or self.saml_settings.SAML_SP_ACS_URL
        if not chosen_acs_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No ACS URL configured for SAML authorization",
            )

        try:
            saml_config = await self._build_saml_config(chosen_acs_url)
            onelogin_settings = OneLogin_Saml2_Settings(
                settings=saml_config, custom_base_path=None
            )

            request_data = self._build_request_data_for_generation(chosen_acs_url)
            auth = OneLogin_Saml2_Auth(request_data, onelogin_settings)

            redirect_url = auth.login(return_to=None)
            request_id = auth.get_last_request_id()
            raw_request_xml = auth.get_last_request_xml()

            if not request_id or not raw_request_xml:
                raise ValueError("Failed to generate SAML AuthnRequest")

            resolved_redirect = self.saml_settings.resolve_redirect_uri(redirect_uri)
            relay_payload = {
                "nonce": secrets.token_urlsafe(32),
                "req": request_id,
                "return_to": resolved_redirect,
            }
            relay_state, expires_at = self._create_relay_state_token(relay_payload)
            redirect_with_state = self._append_relay_state_param(
                redirect_url, relay_state
            )

            logger.info(
                "Generated SAML authorization context",
                acs_url=chosen_acs_url,
                request_id=request_id,
                redirect_uri=resolved_redirect,
            )

            return {
                "sso_url": redirect_url,
                "saml_request": base64.b64encode(
                    raw_request_xml.encode("utf-8")
                ).decode("utf-8"),
                "relay_state": relay_state,
                "expires_at": expires_at,
                "sso_binding": "HTTP-Redirect",
                "redirect_url": redirect_with_state,
            }

        except Exception as exc:
            logger.error("Failed to generate SAML AuthnRequest", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML authorization request generation failed",
            )

    async def generate_sp_metadata(self) -> str:
        """SAML SPメタデータXMLを生成"""

        if not PYTHON3_SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="python3-saml is not available for SAML metadata generation",
            )

        if not self.saml_settings.validate_required_settings():
            logger.error("SAML settings validation failed for metadata generation")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML configuration is incomplete",
            )

        try:
            saml_config = await self._build_saml_config(
                self.saml_settings.SAML_SP_ACS_URL
            )
            onelogin_settings = OneLogin_Saml2_Settings(
                settings=saml_config, custom_base_path=None
            )

            metadata_xml = onelogin_settings.get_sp_metadata()
            errors = onelogin_settings.validate_metadata(metadata_xml)
            if errors:
                logger.error("SAML metadata validation errors", errors=errors)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SAML metadata generation failed",
                )

            return metadata_xml

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to generate SAML metadata", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML metadata generation failed",
            )

    async def get_user_saml_info(
        self,
        *,
        user: UserModel,
        db: AsyncSession,
    ) -> SAMLUserInfoResponse:
        """ユーザーのSAML連携情報を取得"""

        self.user_sso_repository.set_session(db)
        sso_links = await self.user_sso_repository.get_by_user_id(
            user_id=user.id,
            sso_provider="saml",
        )

        if not sso_links:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No SAML link found for this user",
            )

        latest_sso = sso_links[0]

        user_info = SAMLUserInfo(
            subject_id=latest_sso.sso_subject_id,
            email=latest_sso.sso_email or user.email,
            email_verified=True,
            name=latest_sso.sso_display_name or user.full_name,
            preferred_username=user.username,
        )

        response = SAMLUserInfoResponse(
            user_info=user_info,
            saml_provider=latest_sso.sso_provider,
            linked_at=latest_sso.created_at,
            last_login=latest_sso.last_sso_login,
        )

        logger.info(
            "SAML user info response built",
            user_id=user.id,
            saml_subject_id=user_info.subject_id,
        )

        return response

    async def initiate_logout(
        self,
        *,
        request: Request,
        user: UserModel,
        db: AsyncSession,
        redirect_uri: Optional[str] = None,
    ) -> str:
        """IdP向けSAML LogoutRequestを生成"""

        if not PYTHON3_SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="python3-saml is not available for SAML logout",
            )

        if not self.saml_settings.SAML_SP_SLS_URL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML Single Logout service is not configured",
            )

        self.user_sso_repository.set_session(db)
        sso_links = await self.user_sso_repository.get_by_user_id(
            user_id=user.id,
            sso_provider=self.saml_settings.SAML_DEFAULT_PROVIDER,
        )

        if not sso_links:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No SAML link found for this user",
            )

        primary_link = sso_links[0]

        try:
            saml_config = await self._build_saml_config(
                self.saml_settings.SAML_SP_ACS_URL
            )
            onelogin_settings = OneLogin_Saml2_Settings(
                settings=saml_config, custom_base_path=None
            )
            request_data = self._build_request_data_from_http_request(request)
            auth = OneLogin_Saml2_Auth(request_data, onelogin_settings)

            logout_return = self.saml_settings.resolve_redirect_uri(redirect_uri)
            logout_url = auth.logout(
                name_id=primary_link.sso_subject_id,
                session_index=None,
                return_to=logout_return,
            )

            if not logout_url:
                logger.error("SAML logout URL generation returned empty result")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to build SAML logout redirect URL",
                )

            logger.info(
                "Generated SAML logout URL",
                user_id=user.id,
                redirect=logout_url,
            )

            return logout_url

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to initiate SAML logout", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML logout initiation failed",
            )

    async def verify_saml_response(
        self,
        *,
        request: Request,
        saml_response: str,
        relay_state_payload: Dict[str, Any],
        retry_on_signature_error: bool = True,
    ) -> SAMLUserInfo:
        """
        SAML Responseを検証し、ユーザー情報を抽出する

        署名検証エラー時の自動リトライ機能付き
        """

        logger.info(
            "Starting SAML Response verification",
            request_id=relay_state_payload.get("req"),
        )

        if not PYTHON3_SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="python3-saml is not available for SAML verification",
            )

        try:
            if not self.saml_settings.validate_required_settings():
                logger.error("SAML settings validation failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SAML configuration is incomplete",
                )

            request_id = relay_state_payload.get("req")
            if not request_id:
                raise ValidationException("RelayState token missing request identifier")

            # 通常の証明書で検証を試みる
            saml_config = await self._build_saml_config(
                self.saml_settings.SAML_SP_ACS_URL
            )
            onelogin_settings = OneLogin_Saml2_Settings(
                settings=saml_config, custom_base_path=None
            )

            request_data = self._build_request_data_from_http_request(
                request, saml_response
            )
            auth = OneLogin_Saml2_Auth(request_data, onelogin_settings)

            auth.process_response(request_id=request_id)
            errors = auth.get_errors()
            signature_error_occurred = False
            if errors:
                error_reason = auth.get_last_error_reason()
                # 署名関連のエラーかチェック
                if retry_on_signature_error and (
                    "Signature validation failed" in str(error_reason)
                    or "invalid_signature" in str(errors)
                    or any("signature" in str(e).lower() for e in errors)
                ):
                    logger.warning(
                        "Signature verification failed, attempting certificate refresh and retry",
                        errors=errors,
                        reason=error_reason,
                    )
                    signature_error_occurred = True
                else:
                    logger.error(
                        "SAML Response validation failed",
                        errors=errors,
                        reason=error_reason,
                    )
                    raise ValidationException(f"SAML validation failed: {error_reason}")

            # 署名エラーが発生した場合、証明書を更新してリトライ
            if signature_error_occurred:
                try:
                    # 証明書キャッシュをリフレッシュ
                    await self.cert_manager.refresh_on_verification_failure()
                    logger.info(
                        "Certificate cache refreshed, retrying SAML verification"
                    )

                    # 新しい証明書で設定を再構築
                    saml_config = await self._build_saml_config(
                        self.saml_settings.SAML_SP_ACS_URL
                    )
                    onelogin_settings = OneLogin_Saml2_Settings(
                        settings=saml_config, custom_base_path=None
                    )
                    auth = OneLogin_Saml2_Auth(request_data, onelogin_settings)

                    # 再検証
                    auth.process_response(request_id=request_id)
                    errors = auth.get_errors()
                    if errors:
                        error_reason = auth.get_last_error_reason()
                        logger.error(
                            "SAML Response validation failed after retry",
                            errors=errors,
                            reason=error_reason,
                        )
                        raise ValidationException(
                            f"SAML validation failed: {error_reason}"
                        )

                    logger.info("SAML verification succeeded after certificate refresh")
                except Exception as retry_exc:
                    logger.error(
                        "Failed to refresh certificate and retry",
                        error=str(retry_exc),
                    )
                    raise ValidationException(
                        f"SAML signature validation failed even after certificate refresh: {retry_exc}"
                    )

            if not auth.is_authenticated():
                raise ValidationException("SAML authentication failed")

            attributes = auth.get_attributes()
            name_id = auth.get_nameid()
            session_index = auth.get_session_index()

            if not name_id:
                raise ValidationException("Missing NameID in SAML Response")

            attribute_mapping = self.saml_settings.get_attribute_mapping()
            email = self._extract_attribute_value(
                attributes,
                attribute_mapping.get("email", ""),
                default=name_id,
            )

            if not email:
                raise ValidationException("Missing email attribute in SAML Response")

            if not self.saml_settings.is_domain_allowed(email):
                logger.warning("Email domain not allowed", email=email)
                raise ValidationException("Email domain not allowed")

            user_info = SAMLUserInfo(
                subject_id=name_id,
                email=email,
                email_verified=True,
                name=self._extract_attribute_value(
                    attributes, attribute_mapping.get("name", "")
                ),
                given_name=self._extract_attribute_value(
                    attributes, attribute_mapping.get("given_name", "")
                ),
                family_name=self._extract_attribute_value(
                    attributes, attribute_mapping.get("family_name", "")
                ),
                preferred_username=self._extract_attribute_value(
                    attributes,
                    "preferred_username",
                    email.split("@")[0],
                ),
                session_index=session_index,
                attributes=dict(attributes) if attributes else None,
            )

            logger.info(
                "SAML Response verification successful",
                subject_id=user_info.subject_id,
                email=user_info.email,
                session_index=user_info.session_index,
            )

            return user_info

        except ValidationException as exc:
            logger.error("SAML validation failed", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Unexpected error during SAML verification", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML verification failed",
            )

    async def process_logout_request(
        self,
        *,
        request: Request,
        db: AsyncSession,
        post_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """IdP/ブラウザからのSAML Logoutリクエスト・レスポンスを処理"""

        if not PYTHON3_SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="python3-saml is not available for SAML logout",
            )

        try:
            request_data = self._build_request_data_from_http_request(
                request,
                post_data=post_data,
            )
            saml_config = await self._build_saml_config(
                self.saml_settings.SAML_SP_ACS_URL
            )
            onelogin_settings = OneLogin_Saml2_Settings(
                settings=saml_config, custom_base_path=None
            )
            auth = OneLogin_Saml2_Auth(request_data, onelogin_settings)

            redirect_url = auth.process_slo()
            errors = auth.get_errors()
            if errors:
                logger.error("SAML logout processing failed", errors=errors)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to process SAML logout message",
                )

            name_id = auth.get_nameid()
            if name_id:
                await self._cleanup_remote_session(name_id=name_id, db=db)

            final_redirect = redirect_url or self.saml_settings.resolve_redirect_uri(
                None
            )

            logger.info(
                "SAML logout processed",
                name_id=name_id,
                redirect=final_redirect,
            )

            return final_redirect

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Unexpected error during SAML logout", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML logout processing failed",
            )

    async def authenticate_saml_user(
        self, user_info: SAMLUserInfo, db: AsyncSession
    ) -> Tuple[UserModel, SAMLLinkResponse]:
        """
        SAMLユーザー情報を基にローカルユーザーを認証・取得

        処理フロー:
        1. SAML識別子でユーザー連携を検索
        2. 見つからない場合はメールでユーザーを検索
        3. ユーザーが存在しない場合は自動作成（設定による）
        4. SAML連携情報を作成・更新

        Args:
            user_info: 検証済みSAMLユーザー情報
            db: データベースセッション

        Returns:
            (認証されたユーザー, SAML連携レスポンス)

        Raises:
            HTTPException: 認証失敗時
        """
        logger.info(
            "Starting SAML user authentication",
            email=user_info.email,
            subject_id=user_info.subject_id,
        )

        try:
            # リポジトリセッション設定
            self.user_sso_repository.set_session(db)

            # 1. SAML識別子で既存連携を検索
            existing_sso = await self.user_sso_repository.get_by_sso_subject_id(
                sso_subject_id=user_info.subject_id,
                sso_provider=self.saml_settings.SAML_DEFAULT_PROVIDER,
            )

            user: Optional[UserModel] = None
            is_new_user = False
            sso_link_created = False

            if existing_sso:
                # 既存のSAML連携が見つかった場合
                logger.info("Existing SAML link found", user_id=existing_sso.user_id)
                user = await self.user_service.get_user_by_id(
                    existing_sso.user_id,
                    db,
                )
                if not user:
                    logger.error(
                        "Linked user not found for existing SAML",
                        user_sso_id=existing_sso.id,
                        user_id=existing_sso.user_id,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Linked user account is missing",
                    )

                # ログイン情報を更新
                await self.user_sso_repository.update_sso_login(
                    user_sso_id=existing_sso.id,
                    sso_email=user_info.email,
                    sso_display_name=user_info.name,
                )

            else:
                # 2. メールアドレスで既存ユーザーを検索
                user = await self.user_service.get_user_by_email(user_info.email, db)

                if user:
                    # 既存ユーザーに新しいSAML連携を追加
                    logger.info("Linking existing user to SAML", user_id=user.id)
                    await self.user_sso_repository.create_sso_link(
                        user_id=user.id,
                        sso_subject_id=user_info.subject_id,
                        sso_provider=self.saml_settings.SAML_DEFAULT_PROVIDER,
                        sso_email=user_info.email,
                        sso_display_name=user_info.name,
                    )
                    sso_link_created = True

                elif self.saml_settings.SAML_AUTO_CREATE_USERS:
                    # 3. 自動ユーザー作成
                    logger.info("Creating new user from SAML", email=user_info.email)

                    # UserCreateスキーマを構築
                    dummy_password = self._generate_dummy_password()
                    user_create = UserCreate(
                        email=user_info.email,
                        password=dummy_password,  # ダミーパスワード（ログインには使用されない）
                        full_name=user_info.name
                        or f"{user_info.given_name or ''} {user_info.family_name or ''}".strip(),
                        username=user_info.preferred_username
                        or user_info.email.split("@")[0],
                    )

                    # ユーザー作成（ダミーパスワードを設定）
                    user = await self.user_service.create_user(user_create, db)
                    is_new_user = True

                    # SAML連携情報も作成
                    await self.user_sso_repository.create_sso_link(
                        user_id=user.id,
                        sso_subject_id=user_info.subject_id,
                        sso_provider=self.saml_settings.SAML_DEFAULT_PROVIDER,
                        sso_email=user_info.email,
                        sso_display_name=user_info.name,
                    )
                    sso_link_created = True

                else:
                    # ユーザー自動作成が無効
                    logger.warning("User auto-creation disabled", email=user_info.email)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found and auto-creation is disabled",
                    )

            # ユーザーの有効性チェック
            if not user.is_active:
                logger.warning("Inactive user attempted SAML login", user_id=user.id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is inactive",
                )

            # レスポンス構築
            saml_response = SAMLLinkResponse(
                message="SAML authentication successful",
                user_id=user.id,
                saml_subject_id=user_info.subject_id,
                is_new_user=is_new_user,
                linked_at=datetime.now(timezone.utc),
            )

            logger.info(
                "SAML user authentication successful",
                user_id=user.id,
                is_new_user=is_new_user,
                sso_link_created=sso_link_created,
            )

            return user, saml_response

        except HTTPException:
            raise  # HTTP例外は再発生
        except Exception as e:
            logger.error(
                "Unexpected error during SAML user authentication", error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML authentication failed",
            )

    async def create_internal_token_pair(
        self, user: UserModel, db: AsyncSession, device_info: str = None
    ) -> Tuple[str, str, int]:
        """
        認証済みユーザーに対して内部認証トークンを発行

        libkoikiの既存AuthServiceを使用してトークンペアを生成

        Args:
            user: 認証済みユーザー
            db: データベースセッション
            device_info: デバイス情報

        Returns:
            (アクセストークン, リフレッシュトークン, 有効期限)
        """
        logger.info("Creating internal token pair for SAML user", user_id=user.id)

        try:
            (
                access_token,
                refresh_token,
                expires_in,
            ) = await self.auth_service.create_token_pair(
                user=user, db=db, device_info=device_info or "saml-client"
            )

            logger.info("Internal token pair created", user_id=user.id)
            return access_token, refresh_token, expires_in

        except Exception as e:
            logger.error(
                "Failed to create internal token pair", user_id=user.id, error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token generation failed",
            )

    async def _cleanup_remote_session(
        self,
        *,
        name_id: str,
        db: AsyncSession,
    ) -> None:
        """SAML Logout時にローカルセッションを破棄"""

        self.user_sso_repository.set_session(db)
        sso_link = await self.user_sso_repository.get_by_sso_subject_id(
            sso_subject_id=name_id,
            sso_provider=self.saml_settings.SAML_DEFAULT_PROVIDER,
        )

        if not sso_link:
            logger.warning("No SSO link found during logout cleanup", name_id=name_id)
            return

        user = await self.user_service.get_user_by_id(sso_link.user_id, db)
        if not user:
            logger.warning(
                "User not found during logout cleanup",
                user_id=sso_link.user_id,
                name_id=name_id,
            )
            return

        try:
            await self.auth_service.revoke_user_tokens(user.id, db)
            logger.info("Revoked user tokens after SAML logout", user_id=user.id)
        except Exception as exc:
            logger.error(
                "Failed to revoke user tokens during logout cleanup",
                user_id=user.id,
                error=str(exc),
            )

    async def _build_saml_config(
        self, acs_url: str, force_cert_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        OneLogin python3-saml用の設定辞書を構築（動的証明書取得対応）

        Args:
            acs_url: Assertion Consumer Service URL
            force_cert_refresh: 証明書を強制的に再取得するか

        Returns:
            OneLogin_Saml2_Settings用設定辞書
        """
        # 証明書を取得（戦略に応じて動的/静的を自動選択）
        idp_cert, cert_source = await self.cert_manager.get_signing_certificate(
            force_refresh=force_cert_refresh
        )

        logger.debug(
            "Building SAML config with certificate",
            cert_source=cert_source,
            cert_strategy=self.cert_manager.strategy,
        )

        # URLとEntityIDは常に静的設定を使用（ブラウザアクセス可能なURLが必要）
        # メタデータから取得するのは証明書のみ
        #
        # TODO: 本番運用に向けて、メタデータからのURL取得ロジックを再検討
        # Docker環境ではコンテナ内部URL(keycloak:8080)とブラウザアクセス用URL(localhost:8090)の
        # 不一致が発生するため、現在は静的設定を使用している。
        # 本番環境では適切なリバースプロキシ設定により、メタデータURLをそのまま使用できる可能性がある。
        #
        # --- 元の動的URL取得ロジック（コメントアウト） ---
        # if self.cert_manager.metadata_loader:
        #     try:
        #         idp_metadata = await self.cert_manager.get_idp_metadata()
        #         idp_entity_id = idp_metadata.get("entity_id", self.saml_settings.SAML_IDP_ENTITY_ID)
        #         idp_sso_url = idp_metadata.get("sso_url", self.saml_settings.SAML_IDP_SSO_URL)
        #         idp_sls_url = idp_metadata.get("sls_url", self.saml_settings.SAML_IDP_SLS_URL)
        #         logger.debug(
        #             "IdP URLs obtained from metadata",
        #             entity_id=idp_entity_id,
        #             sso_url=idp_sso_url,
        #         )
        #     except Exception as e:
        #         logger.warning(
        #             "Failed to get IdP URLs from metadata, falling back to static config",
        #             error=str(e),
        #         )
        #         idp_entity_id = self.saml_settings.SAML_IDP_ENTITY_ID
        #         idp_sso_url = self.saml_settings.SAML_IDP_SSO_URL
        #         idp_sls_url = self.saml_settings.SAML_IDP_SLS_URL
        # else:
        #     idp_entity_id = self.saml_settings.SAML_IDP_ENTITY_ID
        #     idp_sso_url = self.saml_settings.SAML_IDP_SSO_URL
        #     idp_sls_url = self.saml_settings.SAML_IDP_SLS_URL
        # --- 元の動的URL取得ロジック ここまで ---

        # 現在の実装: 静的設定を使用
        idp_entity_id = self.saml_settings.SAML_IDP_ENTITY_ID
        idp_sso_url = self.saml_settings.SAML_IDP_SSO_URL
        idp_sls_url = self.saml_settings.SAML_IDP_SLS_URL

        logger.debug(
            "Using static configuration for IdP URLs",
            entity_id=idp_entity_id,
            sso_url=idp_sso_url,
            note="Certificate obtained dynamically if metadata enabled",
        )

        # IDP設定を構築
        idp_settings = {
            "entityId": idp_entity_id,
            "singleSignOnService": {
                "url": idp_sso_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": idp_cert,
        }

        # SLS URLがある場合は追加
        if idp_sls_url:
            idp_settings["singleLogoutService"] = {
                "url": idp_sls_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            }

        return {
            "sp": {
                **self.saml_settings.get_saml_sp_settings(),
                "assertionConsumerService": {
                    "url": acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
            },
            "idp": idp_settings,
            "security": self.saml_settings.get_saml_security_settings(),
        }

    def _build_request_data_for_generation(self, acs_url: str) -> Dict[str, Any]:
        """AuthnRequest生成時の疑似リクエストデータを構築"""

        parsed = urlparse(acs_url)
        scheme = parsed.scheme or "https"
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if scheme == "https" else 80)
        return {
            "https": "on" if scheme == "https" else "off",
            "http_host": host,
            "server_port": str(port),
            "script_name": parsed.path or "/",
            "get_data": {},
            "post_data": {},
        }

    def _build_request_data_from_http_request(
        self,
        request: Request,
        saml_response: Optional[str] = None,
        post_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """FastAPIのRequestからpython3-saml用リクエスト辞書を生成"""

        url = request.url
        scheme = url.scheme
        port = url.port or (443 if scheme == "https" else 80)
        request_data = {
            "https": "on" if scheme == "https" else "off",
            "http_host": url.hostname or request.client.host,
            "server_port": str(port),
            "script_name": url.path,
            "get_data": dict(request.query_params),
            "post_data": {},
            "query_string": url.query,
        }

        if saml_response is not None:
            request_data["post_data"] = {"SAMLResponse": saml_response}
        elif post_data is not None:
            request_data["post_data"] = post_data

        return request_data

    def _append_relay_state_param(self, redirect_url: str, relay_state: str) -> str:
        """RelayStateをIdPリダイレクトURLに付与"""

        parsed = urlparse(redirect_url)
        query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query_items["RelayState"] = relay_state
        new_query = urlencode(query_items)
        return urlunparse(parsed._replace(query=new_query))

    def _create_relay_state_token(
        self, payload: Dict[str, Any]
    ) -> Tuple[str, datetime]:
        """RelayState用署名トークンを生成"""

        token, expires_at = self._create_signed_token(payload, self.relay_state_ttl)
        return token, expires_at

    def _validate_relay_state_token(self, relay_state_token: str) -> Dict[str, Any]:
        """RelayStateトークンを検証しペイロードを返す"""

        payload, _ = self._decode_signed_token(relay_state_token, purpose="RelayState")
        if "nonce" not in payload:
            raise ValidationException("RelayState token missing nonce")
        if "req" not in payload:
            raise ValidationException("RelayState token missing request identifier")
        return payload

    def _create_login_ticket(
        self,
        *,
        user: UserModel,
        relay_state_payload: Dict[str, Any],
        user_info: SAMLUserInfo,
    ) -> Tuple[str, datetime, str]:
        """ログインチケットを生成"""

        ticket_id = secrets.token_urlsafe(24)
        payload = {
            "ticket_id": ticket_id,
            "user_id": user.id,
            "relay_nonce": relay_state_payload.get("nonce"),
            "subject_id": user_info.subject_id,
        }
        if user_info.session_index:
            payload["session_index"] = user_info.session_index

        token, expires_at = self._create_signed_token(payload, self.login_ticket_ttl)
        return token, expires_at, ticket_id

    def build_login_redirect_url(
        self, base_redirect_uri: str, login_ticket: str
    ) -> str:
        """ログインチケットを付与したフロントエンド向けリダイレクトURLを生成"""

        parsed = urlparse(base_redirect_uri)
        query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query_items["saml_ticket"] = login_ticket
        new_query = urlencode(query_items)
        return urlunparse(parsed._replace(query=new_query))

    async def handle_acs_request(
        self,
        *,
        request: Request,
        saml_response: str,
        relay_state_token: str,
        db: AsyncSession,
    ) -> Tuple[str, str, datetime, SAMLUserInfo, UserModel]:
        """ACSエンドポイントでの処理を統合"""

        relay_payload = self._validate_relay_state_token(relay_state_token)
        user_info = await self.verify_saml_response(
            request=request,
            saml_response=saml_response,
            relay_state_payload=relay_payload,
        )

        user, _ = await self.authenticate_saml_user(user_info, db)
        redirect_uri = self.saml_settings.resolve_redirect_uri(
            relay_payload.get("return_to")
        )
        login_ticket, expires_at, ticket_id = self._create_login_ticket(
            user=user,
            relay_state_payload=relay_payload,
            user_info=user_info,
        )

        # チケット使用済み管理のためにticket_idを返却側でも利用
        return redirect_uri, login_ticket, expires_at, user_info, user

    async def exchange_login_ticket(
        self,
        *,
        login_ticket: str,
        db: AsyncSession,
        device_info: Optional[str] = None,
    ) -> Tuple[UserModel, str, str, int]:
        """ログインチケットを内部トークンに交換"""

        payload, expires_at = self._decode_signed_token(
            login_ticket, purpose="login ticket"
        )
        ticket_id = payload.get("ticket_id")
        if not ticket_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login ticket missing identifier",
            )

        await self._register_ticket_use(ticket_id, expires_at)

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login ticket missing user information",
            )

        user = await self.user_service.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for login ticket",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive",
            )

        access_token, refresh_token, expires_in = await self.create_internal_token_pair(
            user=user,
            db=db,
            device_info=device_info,
        )

        return user, access_token, refresh_token, expires_in

    async def _register_ticket_use(self, ticket_id: str, expires_at: datetime) -> None:
        """ログインチケットの再利用を防ぐ"""

        now = datetime.now(timezone.utc)
        async with _LOGIN_TICKET_LOCK:
            # 期限切れチケットを掃除
            expired_keys = [
                key for key, exp in _LOGIN_TICKET_CACHE.items() if exp <= now
            ]
            for key in expired_keys:
                _LOGIN_TICKET_CACHE.pop(key, None)

            if ticket_id in _LOGIN_TICKET_CACHE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Login ticket already used",
                )

            _LOGIN_TICKET_CACHE[ticket_id] = expires_at

    @staticmethod
    def _urlsafe_b64decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)

    def _create_signed_token(
        self, payload: Dict[str, Any], ttl: timedelta
    ) -> Tuple[str, datetime]:
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + ttl
        token_payload = dict(payload)
        token_payload["ts"] = int(issued_at.timestamp())
        token_payload["exp"] = int(expires_at.timestamp())

        payload_bytes = json.dumps(token_payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            self.relay_state_signing_key, payload_bytes, hashlib.sha256
        ).digest()

        payload_part = (
            base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
        )
        signature_part = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

        return f"{payload_part}.{signature_part}", expires_at

    def _decode_signed_token(
        self, token: str, *, purpose: str
    ) -> Tuple[Dict[str, Any], datetime]:
        if not token:
            raise ValidationException(f"{purpose} token is required")

        try:
            payload_part, signature_part = token.split(".")
        except ValueError:
            raise ValidationException(f"Invalid {purpose} token format")

        try:
            payload_bytes = self._urlsafe_b64decode(payload_part)
            signature_bytes = self._urlsafe_b64decode(signature_part)
        except Exception as exc:
            logger.warning("Failed to decode token", purpose=purpose, error=str(exc))
            raise ValidationException(f"Invalid {purpose} token encoding") from exc

        expected_signature = hmac.new(
            self.relay_state_signing_key,
            payload_bytes,
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(expected_signature, signature_bytes):
            raise ValidationException(f"Invalid {purpose} token signature")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationException(f"Invalid {purpose} token payload") from exc

        exp_ts = payload.get("exp")
        if not isinstance(exp_ts, (int, float)):
            raise ValidationException(f"{purpose} token missing expiration")

        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            raise ValidationException(f"{purpose} token expired")

        return payload, expires_at

    def _generate_dummy_password(self, length: int = 24) -> str:
        """SAMLユーザー用のダミーパスワードを生成する"""
        import string

        symbols = "!@#$%^&*()-_=+[]{}|;:,.<>/?"
        alphabet = (
            string.ascii_lowercase + string.ascii_uppercase + string.digits + symbols
        )
        while True:
            candidate = "".join(secrets.choice(alphabet) for _ in range(length))
            if check_password_complexity(candidate):
                return candidate

    def _extract_attribute_value(
        self, attributes: Dict[str, list], attribute_name: str, default: str = None
    ) -> Optional[str]:
        """
        SAML属性から値を抽出

        Args:
            attributes: SAML属性辞書
            attribute_name: 属性名
            default: デフォルト値

        Returns:
            属性値（見つからない場合はデフォルト）
        """
        if not attributes or not attribute_name:
            return default

        values = attributes.get(attribute_name, [])
        if values and isinstance(values, list) and len(values) > 0:
            return str(values[0]).strip() or default

        return default
