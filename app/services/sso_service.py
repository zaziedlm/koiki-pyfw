# app/services/sso_service.py
"""
SSO認証サービス

OpenID Connect による外部認証サービスとの連携処理を実装
IDトークンの検証、ユーザー認証、内部トークン発行までの一連の処理を提供
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

    async def verify_id_token(self, id_token: str) -> SSOUserInfo:
        """
        IDトークンを検証し、ユーザー情報を抽出
        
        OpenID Connect標準に従い、以下を検証:
        - JWT署名（JWKSから取得した公開鍵）
        - 発行者 (iss)
        - 対象者 (aud)  
        - 有効期限 (exp)
        - 必須クレーム
        
        Args:
            id_token: OpenID Connect IDトークン
            
        Returns:
            検証済みユーザー情報
            
        Raises:
            HTTPException: トークン検証失敗時
        """
        logger.info("Starting ID token verification")

        try:
            # 設定検証
            if not self.sso_settings.validate_required_settings():
                logger.error("SSO settings validation failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SSO configuration is incomplete"
                )

            # 署名検証
            if self.sso_settings.SSO_SIGNATURE_VALIDATION and self.jwks_uri:
                payload = await self._verify_jwt_with_jwks(id_token)
            else:
                # 開発段階では署名検証を無効化して動作確認を優先
                logger.warning("JWT signature verification disabled (development mode or not configured)")
                payload = jwt.decode(
                    id_token,
                    key=None,  # verify_signature=False 時は key=None を明示
                    options={
                        "verify_signature": False,
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

            # 必須クレーム検証
            if "sub" not in payload:
                raise ValidationException("Missing required 'sub' claim")
            if "email" not in payload:
                raise ValidationException("Missing required 'email' claim")

            # メール検証済み要求
            if self.sso_settings.SSO_REQUIRE_EMAIL_VERIFIED:
                if not payload.get("email_verified", False):
                    raise ValidationException("Email verification required")

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
                locale=payload.get("locale")
            )

            logger.info(
                "ID token verification successful",
                sub=user_info.sub,
                email=user_info.email,
                email_verified=user_info.email_verified
            )
            
            return user_info

        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid ID token"
            )
        except JWKError as e:
            logger.error("JWKS key retrieval failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signature verification failed"
            )
        except ValidationException as e:
            logger.error("Token validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error("Unexpected error during token verification", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token verification failed"
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

    async def _verify_jwt_with_jwks(self, id_token: str) -> dict:
        """JWKS を使って JWT 署名検証とクレーム検証を行う"""
        try:
            header = jwt.get_unverified_header(id_token)
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
            # 開発環境ではフォールバック（設定で制御）
            if self.sso_settings.SSO_DEBUG_MODE and not self.sso_settings.SSO_SIGNATURE_VALIDATION:
                logger.warning("Falling back to unsigned decode due to debug mode")
                return jwt.decode(
                    id_token,
                    key=None,
                    options={"verify_signature": False},
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWKS verification error",
            )
