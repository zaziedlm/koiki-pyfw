# app/services/sso_service.py
"""
SSO認証サービス

OpenID Connect による外部認証サービスとの連携処理を実装
IDトークンの検証、ユーザー認証、内部トークン発行までの一連の処理を提供
"""
from typing import Any, Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta
import asyncio
import base64
import hashlib
import hmac
import json
import secrets
from urllib.parse import urlencode

import structlog
from jose import jwt, JWTError
from jose.exceptions import JWKError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# JWKS クライアント用ライブラリのインポート
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from jwcrypto import jwk
    JWCRYPTO_AVAILABLE = True
except ImportError:
    JWCRYPTO_AVAILABLE = False

from libkoiki.services.user_service import UserService
from libkoiki.services.auth_service import AuthService
from libkoiki.models.user import UserModel
from libkoiki.schemas.user import UserCreate
from libkoiki.core.exceptions import ValidationException

from app.core.sso_config import SSOSettings, get_sso_settings
from app.schemas.sso import SSOUserInfo, SSOLinkResponse
from app.repositories.user_sso_repository import UserSSORepository

logger = structlog.get_logger(__name__)


_JWKS_CACHE: Dict[str, Dict[str, Any]] = {}
_JWKS_CACHE_LOCK = asyncio.Lock()


class SSOService:
    """
    SSO認証サービスクラス
    
    OpenID Connect による外部認証との連携を処理:
    1. IDトークンの署名検証
    2. クレーム抽出・検証
    3. ローカルユーザーとの連携
    4. 内部認証トークンの発行
    """

    def __init__(
        self,
        user_service: UserService,
        auth_service: AuthService,
        sso_settings: SSOSettings = None,
    ):
        self.user_service = user_service
        self.auth_service = auth_service
        self.sso_settings = sso_settings or get_sso_settings()
        self.user_sso_repository = UserSSORepository()

        self.allowed_algorithms = self.sso_settings.get_allowed_algorithms()
        if not self.allowed_algorithms:
            logger.error("No allowed algorithms configured for SSO signature verification")
            raise RuntimeError("SSO allowed algorithms are not configured")

        if not self.sso_settings.SSO_STATE_SIGNING_KEY:
            logger.error("State signing key is not configured for SSO flow")
            raise RuntimeError("SSO state signing key is required")

        self.state_signing_key = self.sso_settings.SSO_STATE_SIGNING_KEY.encode("utf-8")
        self.state_ttl = timedelta(seconds=self.sso_settings.SSO_STATE_TTL_SECONDS)
        self.token_endpoint = self.sso_settings.SSO_TOKEN_ENDPOINT
        self.authorization_endpoint = self.sso_settings.SSO_AUTHORIZATION_ENDPOINT
        self.default_scopes = self.sso_settings.get_scopes()
        self.code_challenge_method = "S256"

        # JWKS設定の初期化
        if self.sso_settings.SSO_JWKS_URI:
            self.jwks_uri = self.sso_settings.SSO_JWKS_URI
            logger.info("JWKS configured", jwks_uri=self.sso_settings.SSO_JWKS_URI)
        else:
            self.jwks_uri = None
        if not JWCRYPTO_AVAILABLE:
            logger.warning("jwcrypto not available; falling back to direct JWK usage")
        if self.sso_settings.SSO_SIGNATURE_VALIDATION and not HTTPX_AVAILABLE:
            logger.warning("httpx not available; cannot fetch JWKS when signature validation is enabled")

    async def verify_id_token(
        self,
        id_token: str,
        *,
        expected_nonce: str,
        state_token: str,
        provider_access_token: Optional[str] = None,
    ) -> SSOUserInfo:
        """
        IDトークンを検証し、ユーザー情報を抽出

        Authorization Code Flow の戻りで受け取った ID トークンに対し、
        OIDC Core 準拠の署名検証とクレーム検証を行う

        Args:
            id_token: OpenID Connect IDトークン
            expected_nonce: 認可リクエストで発行したnonce
            state_token: 認可リクエスト時のstateトークン
            provider_access_token: プロバイダーから返却されたアクセストークン（at_hash検証用）

        Returns:
            検証済みユーザー情報

        Raises:
            HTTPException: トークン検証失敗時
        """
        logger.info("Starting ID token verification")

        try:
            if not expected_nonce:
                raise ValidationException("Nonce is required")

            # 設定検証
            if not self.sso_settings.validate_required_settings():
                logger.error("SSO settings validation failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SSO configuration is incomplete",
                )

            if not self.sso_settings.SSO_SIGNATURE_VALIDATION:
                logger.error("SSO signature validation is disabled but required")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SSO signature validation must be enabled",
                )

            # state/token 整合性検証
            self._validate_state_token(state_token, expected_nonce)

            # 署名検証 + クレーム検証
            payload, signing_alg = await self._verify_jwt_with_jwks(id_token)

            # 必須クレーム検証
            if "sub" not in payload:
                raise ValidationException("Missing required 'sub' claim")
            if "email" not in payload:
                raise ValidationException("Missing required 'email' claim")

            token_nonce = payload.get("nonce")
            if not token_nonce:
                raise ValidationException("Missing required 'nonce' claim")
            if token_nonce != expected_nonce:
                raise ValidationException("Nonce mismatch")

            # メール検証済み要求
            if self.sso_settings.SSO_REQUIRE_EMAIL_VERIFIED and not payload.get("email_verified", False):
                raise ValidationException("Email verification required")

            # aud/azp検証
            audience = payload.get("aud")
            if isinstance(audience, list) and len(audience) > 1:
                azp_claim = payload.get("azp")
                expected_azp = self.sso_settings.get_expected_azp()
                if not azp_claim:
                    raise ValidationException("Missing 'azp' claim for multiple audiences")
                if azp_claim != expected_azp:
                    raise ValidationException("Invalid authorized party")

            # at_hash検証（プロバイダーが返した場合）
            at_hash_claim = payload.get("at_hash")
            if provider_access_token and at_hash_claim:
                if not self._verify_at_hash(provider_access_token, at_hash_claim, signing_alg):
                    raise ValidationException("Invalid access token hash")

            # ドメイン制限チェック
            email = payload["email"]
            if not self.sso_settings.is_domain_allowed(email):
                logger.warning("Email domain not allowed", email=email)
                raise ValidationException("Email domain not allowed")

            # SSOUserInfo構築
            user_info = SSOUserInfo(
                sub=payload["sub"],
                email=email,
                email_verified=payload.get("email_verified", False),
                name=payload.get("name"),
                given_name=payload.get("given_name"),
                family_name=payload.get("family_name"),
                preferred_username=payload.get("preferred_username"),
                picture=payload.get("picture"),
                locale=payload.get("locale"),
            )

            logger.info(
                "ID token verification successful",
                sub=user_info.sub,
                email=user_info.email,
                email_verified=user_info.email_verified,
            )

            return user_info

        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid ID token",
            )
        except JWKError as e:
            logger.error("JWKS key retrieval failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signature verification failed",
            )
        except ValidationException as e:
            logger.error("Token validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during token verification", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token verification failed",
            )

    async def exchange_authorization_code(
        self,
        *,
        authorization_code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Authorization Code をトークンエンドポイントで交換"""

        if not HTTPX_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="httpx is not available for token exchange",
            )

        if not self.token_endpoint:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO token endpoint is not configured",
            )

        if not self.sso_settings.validate_required_settings():
            logger.error("SSO settings validation failed before token exchange")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO configuration is incomplete",
            )

        validated_redirect_uri = self._ensure_redirect_uri_allowed(redirect_uri)

        request_payload = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": validated_redirect_uri,
            "client_id": self.sso_settings.SSO_CLIENT_ID,
            "code_verifier": code_verifier,
        }

        auth = None
        if self.sso_settings.SSO_CLIENT_SECRET:
            auth = httpx.BasicAuth(
                self.sso_settings.SSO_CLIENT_ID,
                self.sso_settings.SSO_CLIENT_SECRET,
            )

        try:
            verify_ssl = not self.sso_settings.SSO_SKIP_SSL_VERIFY
            timeout = httpx.Timeout(5.0, connect=3.0)
            async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
                response = await client.post(
                    self.token_endpoint,
                    data=request_payload,
                    auth=auth,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except Exception as exc:
            logger.error(
                "Authorization code exchange failed",
                error=str(exc),
                token_endpoint=self.token_endpoint,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to exchange authorization code",
            )

        if response.status_code != status.HTTP_200_OK:
            error_detail = "SSO provider token endpoint error"
            try:
                error_payload = response.json()
                error_detail = (
                    error_payload.get("error_description")
                    or error_payload.get("error")
                    or error_detail
                )
            except ValueError:
                if response.text:
                    error_detail = response.text

            logger.error(
                "Token endpoint returned error",
                status_code=response.status_code,
                detail=error_detail,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail,
            )

        try:
            token_payload = response.json()
        except ValueError as exc:
            logger.error("Token endpoint returned invalid JSON", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from SSO provider",
            )

        if "id_token" not in token_payload:
            logger.error("Token endpoint response missing id_token", keys=list(token_payload.keys()))

        logger.info("Authorization code exchange succeeded")
        return token_payload

    def validate_state(self, state_token: str, expected_nonce: str) -> None:
        """外部公開用のstate検証ラッパー"""
        logger.info("Validating SSO state token")
        self._validate_state_token(state_token, expected_nonce)

    def generate_authorization_context(
        self,
        *,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """state/nonceを生成し、認可リクエストに必要な情報を返す"""

        if not self.authorization_endpoint:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO authorization endpoint is not configured",
            )

        chosen_redirect_uri = redirect_uri or self.sso_settings.get_default_redirect_uri()
        if not chosen_redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No redirect_uri configured for SSO authorization",
            )

        validated_redirect_uri = self._ensure_redirect_uri_allowed(chosen_redirect_uri)

        nonce = secrets.token_urlsafe(32)
        state_token, expires_at = self._create_state_token(nonce)

        base_parameters = {
            "response_type": "code",
            "client_id": self.sso_settings.SSO_CLIENT_ID,
            "redirect_uri": validated_redirect_uri,
            "scope": self.default_scopes,
            "state": state_token,
            "nonce": nonce,
        }

        base_query = urlencode(base_parameters)
        authorization_base_url = f"{self.authorization_endpoint}?{base_query}"

        logger.info(
            "Generated authorization context",
            redirect_uri=validated_redirect_uri,
            nonce=nonce,
        )

        return {
            "authorization_endpoint": self.authorization_endpoint,
            "authorization_base_url": authorization_base_url,
            "response_type": base_parameters["response_type"],
            "client_id": base_parameters["client_id"],
            "redirect_uri": base_parameters["redirect_uri"],
            "scope": base_parameters["scope"],
            "state": state_token,
            "nonce": nonce,
            "expires_at": expires_at,
            "code_challenge_method": self.code_challenge_method,
        }

    async def authenticate_sso_user(
        self, 
        user_info: SSOUserInfo, 
        db: AsyncSession
    ) -> Tuple[UserModel, SSOLinkResponse]:
        """
        SSO ユーザー情報を基にローカルユーザーを認証・取得
        
        処理フロー:
        1. SSO識別子でユーザー連携を検索
        2. 見つからない場合はメールでユーザーを検索
        3. ユーザーが存在しない場合は自動作成（設定による）
        4. SSO連携情報を作成・更新
        
        Args:
            user_info: 検証済みSSO ユーザー情報
            db: データベースセッション
            
        Returns:
            (認証されたユーザー, SSO連携レスポンス)
            
        Raises:
            HTTPException: 認証失敗時
        """
        logger.info("Starting SSO user authentication", email=user_info.email, sub=user_info.sub)

        try:
            # リポジトリセッション設定
            self.user_sso_repository.set_session(db)

            # 1. SSO識別子で既存連携を検索
            existing_sso = await self.user_sso_repository.get_by_sso_subject_id(
                sso_subject_id=user_info.sub,
                sso_provider=self.sso_settings.SSO_DEFAULT_PROVIDER
            )

            user: Optional[UserModel] = None
            is_new_user = False
            sso_link_created = False

            if existing_sso:
                # 既存のSSO連携が見つかった場合
                logger.info("Existing SSO link found", user_id=existing_sso.user_id)
                user = existing_sso.user
                
                # ログイン情報を更新
                await self.user_sso_repository.update_sso_login(
                    user_sso_id=existing_sso.id,
                    sso_email=user_info.email,
                    sso_display_name=user_info.name
                )
                
            else:
                # 2. メールアドレスで既存ユーザーを検索
                user = await self.user_service.get_by_email(user_info.email, db)
                
                if user:
                    # 既存ユーザーに新しいSSO連携を追加
                    logger.info("Linking existing user to SSO", user_id=user.id)
                    await self.user_sso_repository.create_sso_link(
                        user_id=user.id,
                        sso_subject_id=user_info.sub,
                        sso_provider=self.sso_settings.SSO_DEFAULT_PROVIDER,
                        sso_email=user_info.email,
                        sso_display_name=user_info.name
                    )
                    sso_link_created = True
                    
                elif self.sso_settings.SSO_AUTO_CREATE_USERS:
                    # 3. 自動ユーザー作成
                    logger.info("Creating new user from SSO", email=user_info.email)
                    
                    # UserCreateスキーマ構築
                    import secrets
                    dummy_password = secrets.token_urlsafe(32)  # SSO ユーザー用ダミーパスワード
                    user_create = UserCreate(
                        email=user_info.email,
                        password=dummy_password,  # ダミーパスワード（ログインには使用されない）
                        full_name=user_info.name or f"{user_info.given_name or ''} {user_info.family_name or ''}".strip(),
                        username=user_info.preferred_username or user_info.email.split("@")[0]
                    )
                    
                    # ユーザー作成（ダミーパスワードを設定）
                    user = await self.user_service.create_user(user_create, db)
                    is_new_user = True
                    
                    # SSO連携情報も作成
                    await self.user_sso_repository.create_sso_link(
                        user_id=user.id,
                        sso_subject_id=user_info.sub,
                        sso_provider=self.sso_settings.SSO_DEFAULT_PROVIDER,
                        sso_email=user_info.email,
                        sso_display_name=user_info.name
                    )
                    sso_link_created = True
                    
                else:
                    # ユーザー自動作成が無効
                    logger.warning("User auto-creation disabled", email=user_info.email)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found and auto-creation is disabled"
                    )

            # ユーザーの有効性チェック
            if not user.is_active:
                logger.warning("Inactive user attempted SSO login", user_id=user.id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is inactive"
                )

            # レスポンス構築
            sso_response = SSOLinkResponse(
                message="SSO authentication successful",
                user_id=user.id,
                sso_subject_id=user_info.sub,
                is_new_user=is_new_user,
                linked_at=datetime.now(timezone.utc)
            )

            logger.info(
                "SSO user authentication successful",
                user_id=user.id,
                is_new_user=is_new_user,
                sso_link_created=sso_link_created
            )

            return user, sso_response

        except HTTPException:
            raise  # HTTP例外は再発生
        except Exception as e:
            logger.error("Unexpected error during SSO user authentication", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSO authentication failed"
            )

    async def create_internal_token_pair(
        self, 
        user: UserModel, 
        db: AsyncSession,
        device_info: str = None
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
        logger.info("Creating internal token pair for SSO user", user_id=user.id)

        try:
            access_token, refresh_token, expires_in = await self.auth_service.create_token_pair(
                user=user, 
                db=db, 
                device_info=device_info or "sso-client"
            )

            logger.info("Internal token pair created", user_id=user.id)
            return access_token, refresh_token, expires_in

        except Exception as e:
            logger.error("Failed to create internal token pair", user_id=user.id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token generation failed"
            )

    def _validate_state_token(self, state_token: str, expected_nonce: str) -> None:
        """stateパラメータが改ざんされていないかとnonceの一致を検証"""
        if not state_token:
            raise ValidationException("State parameter is required")

        try:
            payload_part, signature_part = state_token.split(".")
        except ValueError:
            raise ValidationException("Invalid state token format")

        try:
            payload_bytes = self._urlsafe_b64decode(payload_part)
            signature_bytes = self._urlsafe_b64decode(signature_part)
        except Exception as exc:
            logger.warning("Failed to decode state token", error=str(exc))
            raise ValidationException("Invalid state token encoding") from exc

        expected_signature = hmac.new(
            self.state_signing_key,
            payload_bytes,
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(expected_signature, signature_bytes):
            raise ValidationException("Invalid state token signature")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationException("Invalid state token payload") from exc

        token_nonce = payload.get("nonce")
        timestamp = payload.get("ts")

        if token_nonce != expected_nonce:
            raise ValidationException("State token nonce mismatch")

        if not isinstance(timestamp, (int, float)):
            raise ValidationException("State token missing timestamp")

        issued_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        if now - issued_at > self.state_ttl:
            raise ValidationException("State token expired")

    def _create_state_token(self, nonce: str, issued_at: Optional[datetime] = None) -> Tuple[str, datetime]:
        """nonceと時刻から署名済みstateトークンを生成"""
        issued_at = issued_at or datetime.now(timezone.utc)
        payload_bytes = json.dumps(
            {"nonce": nonce, "ts": int(issued_at.timestamp())},
            separators=(",", ":"),
        ).encode("utf-8")

        payload_part = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
        signature = hmac.new(self.state_signing_key, payload_bytes, hashlib.sha256).digest()
        signature_part = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

        state_token = f"{payload_part}.{signature_part}"
        expires_at = issued_at + self.state_ttl
        return state_token, expires_at

    @staticmethod
    def _urlsafe_b64decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)

    @staticmethod
    def _verify_at_hash(access_token: str, at_hash_value: str, signing_alg: str) -> bool:
        alg = signing_alg.upper()
        if alg.endswith("256"):
            digest = hashlib.sha256(access_token.encode("utf-8")).digest()
        elif alg.endswith("384"):
            digest = hashlib.sha384(access_token.encode("utf-8")).digest()
        elif alg.endswith("512"):
            digest = hashlib.sha512(access_token.encode("utf-8")).digest()
        else:
            logger.warning("Unsupported signing algorithm for at_hash verification", alg=signing_alg)
            return False

        cut = len(digest) // 2
        expected_hash = base64.urlsafe_b64encode(digest[:cut]).decode("ascii").rstrip("=")
        return hmac.compare_digest(expected_hash, at_hash_value)

    def _ensure_redirect_uri_allowed(self, redirect_uri: str) -> str:
        if not redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="redirect_uri is required",
            )

        if not self.sso_settings.is_redirect_uri_allowed(redirect_uri):
            logger.warning("Redirect URI not allowed", redirect_uri=redirect_uri)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="redirect_uri is not allowed",
            )

        return redirect_uri

    # --- 内部ユーティリティ: JWKS 検証関連 ---
    async def _fetch_jwks(self, *, force_refresh: bool = False) -> dict:
        """JWKS を取得（アプリケーション全体での簡易キャッシュ付き）"""
        if not self.jwks_uri:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWKS URI is not configured",
            )

        now = datetime.now(timezone.utc)
        ttl = timedelta(seconds=self.sso_settings.SSO_TOKEN_CACHE_TTL)

        if not force_refresh:
            async with _JWKS_CACHE_LOCK:
                cache_entry = _JWKS_CACHE.get(self.jwks_uri)
                if cache_entry:
                    fetched_at = cache_entry.get("fetched_at")
                    jwks = cache_entry.get("jwks")
                    if fetched_at and jwks and now - fetched_at < ttl:
                        return jwks

        if not HTTPX_AVAILABLE:  # ライブラリ未導入
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="httpx is not available for JWKS retrieval",
            )

        try:
            verify_ssl = not self.sso_settings.SSO_SKIP_SSL_VERIFY
            timeout = httpx.Timeout(5.0, connect=3.0)
            async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
                resp = await client.get(self.jwks_uri)
                resp.raise_for_status()
                jwks = resp.json()
        except Exception as e:
            logger.error("Failed to fetch JWKS", error=str(e), jwks_uri=self.jwks_uri)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to retrieve JWKS for signature verification",
            )

        async with _JWKS_CACHE_LOCK:
            _JWKS_CACHE[self.jwks_uri] = {"jwks": jwks, "fetched_at": now}
        return jwks

    async def _verify_jwt_with_jwks(self, id_token: str) -> Tuple[dict, str]:
        """JWKS を使って JWT 署名検証とクレーム検証を行う"""
        try:
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")
            alg = header.get("alg")
            if not kid or not alg:
                raise ValidationException("Missing 'kid' or 'alg' in token header")

            if alg not in self.allowed_algorithms:
                raise ValidationException("Disallowed JWT algorithm")

            jwks = await self._fetch_jwks()
            keys = jwks.get("keys", [])
            key_dict = next((k for k in keys if k.get("kid") == kid), None)
            if not key_dict:
                logger.info("Refreshing JWKS due to missing kid", kid=kid)
                jwks = await self._fetch_jwks(force_refresh=True)
                keys = jwks.get("keys", [])
                key_dict = next((k for k in keys if k.get("kid") == kid), None)
            if not key_dict:
                logger.warning("No matching JWK found for kid", kid=kid)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find matching JWK for token",
                )

            # できれば jwcrypto で PEM にして decode
            key_for_decode = None
            if JWCRYPTO_AVAILABLE:
                try:
                    jwk_obj = jwk.JWK(**key_dict)
                    pem_bytes = jwk_obj.export_to_pem(public_key=True, private_key=False)
                    key_for_decode = pem_bytes
                except Exception as e:
                    logger.warning("jwcrypto PEM export failed; will try direct JWK decode", error=str(e))
                    key_for_decode = key_dict
            else:
                # jwcrypto 未インストール: python-jose に JWK を直接渡す（対応環境のみ）
                key_for_decode = key_dict

            payload = jwt.decode(
                id_token,
                key=key_for_decode,
                algorithms=[alg],
                options={
                    "verify_signature": True,
                    "verify_exp": self.sso_settings.SSO_EXPIRY_VALIDATION,
                    "verify_aud": self.sso_settings.SSO_AUDIENCE_VALIDATION,
                    "verify_iss": self.sso_settings.SSO_ISSUER_VALIDATION,
                },
                audience=(
                    self.sso_settings.SSO_CLIENT_ID
                    if self.sso_settings.SSO_AUDIENCE_VALIDATION
                    else None
                ),
                issuer=(
                    self.sso_settings.SSO_ISSUER_URL
                    if self.sso_settings.SSO_ISSUER_VALIDATION
                    else None
                ),
                leeway=self.sso_settings.SSO_CLOCK_SKEW_SECONDS,
            )
            return payload, alg

        except HTTPException:
            raise
        except JWTError as e:
            logger.error("JWT signature verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signature verification failed",
            )
        except Exception as e:
            logger.error("Unexpected error during JWKS verification", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWKS verification error",
            )
