# app/services/sso_service.py
"""
SSO 認証サービス群。

OpenID Connect のアクセストークン検証と後段処理の連携をまとめて提供する。
"""


from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta

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


class SSOService:
    """
    SSO 認証サービスの実装クラス。

    OpenID Connect 連携の主な流れ:
    1. アクセストークン検証（JWKS 検証または RFC 7662 イントロスペクション）。
    2. アカウントの検索・プロビジョニング。
    3. ローカルアカウントとの紐付け。
    4. KOIKI 内部トークンの発行。
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

        self.allowed_audiences = self.sso_settings.get_allowed_audiences()
        if not self.allowed_audiences and self.sso_settings.SSO_CLIENT_ID:
            self.allowed_audiences = [self.sso_settings.SSO_CLIENT_ID]
        self.allow_sub_update = self.sso_settings.SSO_ALLOW_SUB_UPDATE
        self.introspection_auth_mode = (
            self.sso_settings.SSO_INTROSPECTION_AUTH_MODE or "basic"
        ).lower()
        self.introspection_token = self.sso_settings.SSO_INTROSPECTION_TOKEN

        self.introspection_enabled = (
            self.sso_settings.SSO_INTROSPECTION_ENABLED
            and bool(self.sso_settings.SSO_INTROSPECTION_ENDPOINT)
        )
        if self.introspection_enabled:
            logger.info(
                "SSO access token introspection enabled",
                endpoint=self.sso_settings.SSO_INTROSPECTION_ENDPOINT,
            )
        elif self.sso_settings.SSO_INTROSPECTION_ENABLED:
            logger.warning(
                "SSO introspection enabled but endpoint is not configured",
            )
        if self.introspection_enabled and not HTTPX_AVAILABLE:
            logger.warning(
                "httpx not available; access token introspection cannot be performed",
            )

        # JWKS設定の初期化
        if self.sso_settings.SSO_JWKS_URI:
            self.jwks_uri = self.sso_settings.SSO_JWKS_URI
            # 簡易キャッシュ: {"fetched_at": datetime, "jwks": dict}
            self.jwks_cache: dict = {}
            logger.info("JWKS configured", jwks_uri=self.sso_settings.SSO_JWKS_URI)
        else:
            self.jwks_uri = None
            self.jwks_cache = {}
        if not JWCRYPTO_AVAILABLE:
            logger.warning("jwcrypto not available, JWT signature verification will use fallback path")
        if self.sso_settings.SSO_SIGNATURE_VALIDATION and not HTTPX_AVAILABLE:
            logger.warning("httpx not available; cannot fetch JWKS when signature validation is enabled")

    async def verify_access_token(self, access_token: str) -> SSOUserInfo:
        """
        OAuth2 アクセストークンを検証し、正規化したユーザー情報を構築する。

        上流の BFF が ID トークンの検証を済ませている前提で、ここでは
        JWKS を用いた署名検証または RFC 7662 ベースのイントロスペクションを行い、
        KOIKI で扱う SSO ユーザーモデルへ落とし込む。
        """

        logger.info("Starting access token verification")

        try:
            if not access_token:
                raise ValidationException("Access token is required")

            if not self.sso_settings.validate_required_settings():
                logger.error("SSO settings validation failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SSO configuration is incomplete",
                )

            expected_audiences = (
                list(self.allowed_audiences)
                if self.sso_settings.SSO_AUDIENCE_VALIDATION and self.allowed_audiences
                else []
            )

            if self.introspection_enabled:
                claims = await self._introspect_access_token(access_token)
            else:
                if self.sso_settings.SSO_SIGNATURE_VALIDATION and self.jwks_uri:
                    claims = await self._decode_jwt_with_jwks(
                        access_token,
                        expected_audiences if expected_audiences else None,
                    )
                else:
                    logger.warning(
                        "JWT signature verification disabled (development mode or not configured)"
                    )
                    options = {
                        "verify_signature": False,
                        "verify_exp": self.sso_settings.SSO_EXPIRY_VALIDATION,
                        "verify_aud": bool(expected_audiences)
                        and self.sso_settings.SSO_AUDIENCE_VALIDATION,
                        "verify_iss": self.sso_settings.SSO_ISSUER_VALIDATION,
                    }
                    claims = jwt.decode(
                        access_token,
                        key=None,
                        options=options,
                        audience=(expected_audiences if options["verify_aud"] else None),
                        issuer=(
                            self.sso_settings.SSO_ISSUER_URL
                            if self.sso_settings.SSO_ISSUER_VALIDATION
                            else None
                        ),
                        leeway=self.sso_settings.SSO_CLOCK_SKEW_SECONDS,
                    )

            if not isinstance(claims, dict):
                raise ValidationException("Invalid token payload")

            claims = dict(claims)

            if "active" in claims:
                if not claims.get("active", False):
                    raise ValidationException("Access token is not active")
                claims.pop("active", None)

            if isinstance(claims.get("scope"), str):
                claims["scope"] = [scope for scope in claims["scope"].split() if scope]

            if "sub" not in claims or not claims.get("sub"):
                raise ValidationException("Missing required 'sub' claim")

            self._validate_audience(claims)

            need_userinfo = False
            if self.sso_settings.SSO_USER_INFO_ENDPOINT:
                if not claims.get("email"):
                    need_userinfo = True
                elif (
                    self.sso_settings.SSO_REQUIRE_EMAIL_VERIFIED
                    and "email_verified" not in claims
                ):
                    need_userinfo = True

            if need_userinfo:
                userinfo_claims = await self._fetch_user_info(access_token)
                if userinfo_claims:
                    claims = self._merge_claims(claims, userinfo_claims)

            email = claims.get("email")
            if not email:
                raise ValidationException("Missing required 'email' claim")

            email_verified_raw = claims.get("email_verified")
            email_verified = None
            if email_verified_raw is not None:
                email_verified = self._coerce_bool(email_verified_raw)
                claims["email_verified"] = email_verified
            else:
                claims.pop("email_verified", None)

            if self.sso_settings.SSO_REQUIRE_EMAIL_VERIFIED:
                if email_verified is None:
                    raise ValidationException("Email verification status unavailable")
                if not email_verified:
                    raise ValidationException("Email verification required")

            if email_verified is None:
                email_verified = False
                claims["email_verified"] = email_verified

            if not self.sso_settings.is_domain_allowed(email):
                logger.warning("Email domain not allowed", email=email)
                raise ValidationException("Email domain not allowed")

            user_info = SSOUserInfo(
                sub=claims["sub"],
                email=email,
                email_verified=email_verified,
                name=claims.get("name"),
                given_name=claims.get("given_name"),
                family_name=claims.get("family_name"),
                preferred_username=claims.get("preferred_username"),
                picture=claims.get("picture"),
                locale=claims.get("locale"),
            )

            logger.info(
                "Access token verification successful",
                sub=user_info.sub,
                email=user_info.email,
                email_verified=user_info.email_verified,
            )

            return user_info

        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
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
                if (
                    self.allow_sub_update
                    and existing_sso.sso_subject_id != user_info.sub
                ):
                    logger.info("Updating SSO subject binding", old_subject=existing_sso.sso_subject_id, new_subject=user_info.sub)
                    existing_sso.sso_subject_id = user_info.sub
                    await self.user_sso_repository.update(existing_sso)
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

    async def _introspect_access_token(self, access_token: str) -> dict:
        """
        設定済みのイントロスペクション エンドポイントを呼び出し、アクセストークンの有効性を確認する。
        """

        if not HTTPX_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="httpx is required for token introspection",
            )

        endpoint = self.sso_settings.SSO_INTROSPECTION_ENDPOINT
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token introspection endpoint is not configured",
            )

        mode = self.introspection_auth_mode

        try:
            verify_ssl = not self.sso_settings.SSO_SKIP_SSL_VERIFY
            timeout = httpx.Timeout(5.0, connect=3.0)
            data = {"token": access_token, "token_type_hint": "access_token"}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            auth = None

            if mode == "basic":
                if self.sso_settings.SSO_CLIENT_ID and self.sso_settings.SSO_CLIENT_SECRET:
                    auth = (
                        self.sso_settings.SSO_CLIENT_ID,
                        self.sso_settings.SSO_CLIENT_SECRET,
                    )
                else:
                    logger.warning("Client secret is required for basic introspection auth")
            elif mode == "bearer":
                if self.introspection_token:
                    headers["Authorization"] = f"Bearer {self.introspection_token}"
                else:
                    logger.warning("Introspection bearer token is not configured; falling back to unauthenticated request")
            elif mode != "none":
                logger.warning("Unknown introspection auth mode", mode=mode)

            if self.sso_settings.SSO_CLIENT_ID and mode in {"none", "bearer"}:
                data.setdefault("client_id", self.sso_settings.SSO_CLIENT_ID)
            if mode == "none" and self.sso_settings.SSO_CLIENT_SECRET:
                data.setdefault("client_secret", self.sso_settings.SSO_CLIENT_SECRET)

            async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
                response = await client.post(
                    endpoint,
                    data=data,
                    headers=headers,
                    auth=auth,
                )
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict) and isinstance(payload.get("scope"), str):
                    payload["scope"] = [scope for scope in payload["scope"].split() if scope]
                return payload
        except httpx.HTTPStatusError as e:
            logger.error(
                "Token introspection rejected by identity provider",
                status_code=e.response.status_code,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token introspection failed",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token introspection error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token introspection error",
            )

    async def _fetch_user_info(self, access_token: str) -> dict:
        """
        設定されたユーザー情報エンドポイントから追加クレームを取得する。
        """

        endpoint = self.sso_settings.SSO_USER_INFO_ENDPOINT
        if not endpoint:
            return {}

        if not HTTPX_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="httpx is required to call the user info endpoint",
            )

        try:
            verify_ssl = not self.sso_settings.SSO_SKIP_SSL_VERIFY
            timeout = httpx.Timeout(5.0, connect=3.0)
            headers = {"Authorization": f"Bearer {access_token}"}
            async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
                response = await client.get(
                    endpoint,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "User info endpoint rejected the access token",
                status_code=e.response.status_code,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token rejected by user info endpoint",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("User info retrieval error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user info",
            )

    @staticmethod
    def _coerce_bool(value: object) -> bool:
        """
        文字列や数値で返される真偽値を正規化するユーティリティ。
        """

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes"}
        if isinstance(value, (int, float)):
            return bool(value)
        return bool(value)

    def _merge_claims(self, base: dict, additional: dict) -> dict:
        """
        プロバイダーから得たクレームを結合し、既存値を尊重しつつメール系のみ上書きする。
        """

        merged = dict(base)
        for key, value in additional.items():
            if value is None:
                continue
            if key == "sub":
                if merged.get("sub") and not self.allow_sub_update:
                    continue
                merged["sub"] = value
            elif key == "email":
                merged["email"] = value
            elif key == "email_verified":
                merged["email_verified"] = self._coerce_bool(value)
            else:
                merged.setdefault(key, value)
        return merged

    def _validate_audience(self, claims: dict) -> None:
        """アクセストークン内の aud が許可リストに含まれるか検証する。"""
        if not self.sso_settings.SSO_AUDIENCE_VALIDATION:
            return
        if not self.allowed_audiences:
            return

        token_aud = claims.get("aud") or claims.get("client_id")
        if token_aud is None:
            raise ValidationException("Audience not provided in token")

        if isinstance(token_aud, str):
            token_auds = [token_aud]
        elif isinstance(token_aud, (list, tuple, set)):
            token_auds = [str(aud) for aud in token_aud if aud]
        else:
            token_auds = [str(token_aud)] if token_aud else []

        if not any(aud in self.allowed_audiences for aud in token_auds):
            raise ValidationException("Audience not allowed")

    # --- 内部ユーティリティ: JWKS 検証関連 ---
    async def _fetch_jwks(self) -> dict:
        """JWKS を取得（簡易キャッシュ付き）"""
        if not self.jwks_uri:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWKS URI is not configured",
            )

        # キャッシュが有効で、TTL 内ならキャッシュを返す
        now = datetime.now(timezone.utc)
        if self.jwks_cache:
            fetched_at: datetime = self.jwks_cache.get("fetched_at")
            jwks: dict = self.jwks_cache.get("jwks")
            if fetched_at and jwks:
                ttl = timedelta(seconds=self.sso_settings.SSO_TOKEN_CACHE_TTL)
                if now - fetched_at < ttl:
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

        # キャッシュ保存
        self.jwks_cache = {"jwks": jwks, "fetched_at": now}
        return jwks

    async def _decode_jwt_with_jwks(self, token: str, audiences: Optional[list[str]] = None) -> dict:
        """JWKS を用いて JWT の署名とクレームを検証する。"""
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg")
            if not kid or not alg:
                raise ValidationException("Missing 'kid' or 'alg' in token header")

            jwks = await self._fetch_jwks()
            keys = jwks.get("keys", [])
            key_dict = next((k for k in keys if k.get("kid") == kid), None)
            if not key_dict:
                logger.warning("No matching JWK found for kid", kid=kid)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find matching JWK for token",
                )

            key_for_decode = None
            if JWCRYPTO_AVAILABLE:
                try:
                    jwk_obj = jwk.JWK(**key_dict)
                    pem_bytes = jwk_obj.export_to_pem(public_key=True, private_key=False)
                    key_for_decode = pem_bytes
                except Exception as e:
                    logger.warning(
                        "jwcrypto PEM export failed; will try direct JWK decode",
                        error=str(e),
                    )
                    key_for_decode = key_dict
            else:
                key_for_decode = key_dict

            verify_aud = self.sso_settings.SSO_AUDIENCE_VALIDATION and bool(audiences)

            payload = jwt.decode(
                token,
                key=key_for_decode,
                algorithms=[alg],
                options={
                    "verify_signature": True,
                    "verify_exp": self.sso_settings.SSO_EXPIRY_VALIDATION,
                    "verify_aud": verify_aud,
                    "verify_iss": self.sso_settings.SSO_ISSUER_VALIDATION,
                },
                audience=(audiences if verify_aud else None),
                issuer=(
                    self.sso_settings.SSO_ISSUER_URL
                    if self.sso_settings.SSO_ISSUER_VALIDATION
                    else None
                ),
                leeway=self.sso_settings.SSO_CLOCK_SKEW_SECONDS,
            )
            return payload

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
            if self.sso_settings.SSO_DEBUG_MODE and not self.sso_settings.SSO_SIGNATURE_VALIDATION:
                logger.warning("Falling back to unsigned decode due to debug mode")
                return jwt.decode(
                    token,
                    key=None,
                    options={"verify_signature": False},
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWKS verification error",
            )

