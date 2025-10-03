# app/core/saml_config.py
"""
SAML (Security Assertion Markup Language) 設定管理

SAML 2.0 による外部認証サービスとの連携に必要な
設定値を管理します。環境変数から読み込み、適切なデフォルト値を提供。
"""

from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class SAMLSettings(BaseSettings):
    """
    SAML認証設定クラス

    SAML 2.0 Identity Provider との連携に必要な設定値を定義
    環境変数 (.env ファイル) から設定を読み込む
    """

    # === 必須設定 ===
    SAML_SP_ENTITY_ID: str = ""
    """SAML Service Provider エンティティID - アプリケーションの識別子"""

    SAML_IDP_ENTITY_ID: str = ""
    """SAML Identity Provider エンティティID - IdPの識別子"""

    SAML_IDP_SSO_URL: str = ""
    """SAML IdP SSO エンドポイント - 認証リクエストの送信先"""

    SAML_IDP_SLS_URL: str = ""
    """SAML IdP Single Logout Service エンドポイント"""

    SAML_IDP_X509_CERT: str = ""
    """SAML IdP X.509 証明書 - SAML Response署名検証用"""

    SAML_SP_X509_CERT: str = ""
    """SAML SP X.509 証明書 - SAML Request署名用（オプション）"""

    SAML_SP_PRIVATE_KEY: str = ""
    """SAML SP 秘密鍵 - SAML Request署名用（オプション）"""

    # === エンドポイント設定 ===
    SAML_SP_ACS_URL: str = ""
    """SAML SP Assertion Consumer Service URL - SAML Responseの受信先"""

    SAML_SP_SLS_URL: str = ""
    """SAML SP Single Logout Service URL - ログアウト応答の受信先"""

    SAML_DEFAULT_REDIRECT_URI: str = ""
    """SAML フロー完了後にブラウザを戻すリダイレクトURI（未指定時は / ）"""

    SAML_ALLOWED_REDIRECT_URIS: Optional[str] = None
    """許可するリダイレクトURI一覧（カンマ区切り）。未設定時はデフォルトURIのみ許可"""

    # === オプション設定 ===
    SAML_AUTO_CREATE_USERS: bool = True
    """初回SAML ログイン時の自動ユーザー作成フラグ"""

    SAML_DEFAULT_PROVIDER: str = "saml"
    """デフォルトSAMLプロバイダー名"""

    SAML_REQUIRE_EMAIL_VERIFIED: bool = False
    """メール検証済み要求フラグ（SAMLでは通常IdP側で検証済み）"""

    SAML_ALLOWED_DOMAINS: Optional[str] = None
    """許可ドメインリスト (カンマ区切り)。Noneの場合は全ドメイン許可"""

    # === 署名・暗号化設定 ===
    SAML_SIGN_REQUESTS: bool = False
    """SAML AuthnRequest署名の有効化"""

    SAML_SIGN_RESPONSES: bool = True
    """SAML Response署名検証の有効化"""

    SAML_SIGN_ASSERTIONS: bool = True
    """SAML Assertion署名検証の有効化"""

    SAML_ENCRYPT_ASSERTIONS: bool = False
    """SAML Assertion暗号化の有効化"""

    SAML_SIGNATURE_ALGORITHM: str = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
    """SAML署名アルゴリズム"""

    SAML_DIGEST_ALGORITHM: str = "http://www.w3.org/2001/04/xmlenc#sha256"
    """SAMLダイジェストアルゴリズム"""

    # === 属性マッピング設定 ===
    SAML_ATTRIBUTE_MAPPING: str = ""
    """SAML属性マッピング設定（JSON形式文字列）"""

    SAML_DEFAULT_ATTRIBUTE_EMAIL: str = (
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    )
    """デフォルトメール属性名"""

    SAML_DEFAULT_ATTRIBUTE_NAME: str = (
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
    )
    """デフォルト名前属性名"""

    SAML_DEFAULT_ATTRIBUTE_GIVEN_NAME: str = (
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
    )
    """デフォルト名属性名"""

    SAML_DEFAULT_ATTRIBUTE_SURNAME: str = (
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
    )
    """デフォルト姓属性名"""

    # === セキュリティ設定 ===
    SAML_NAME_ID_FORMAT: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    """SAML NameID フォーマット"""

    SAML_AUTHN_CONTEXT_CLASS: str = (
        "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"
    )
    """SAML AuthnContext クラス"""

    SAML_ASSERTION_TTL: int = 300
    """SAML Assertion 有効期限（秒）"""

    SAML_CLOCK_SKEW_SECONDS: int = 30
    """SAML時刻ずれ許容範囲（秒）"""

    SAML_RELAY_STATE_TTL_SECONDS: int = 600
    """RelayState token の許容有効期限（秒）"""

    SAML_RELAY_STATE_SIGNING_KEY: str = ""
    """RelayState検証用のHMACシークレット"""

    SAML_LOGIN_TICKET_TTL_SECONDS: int = 120
    """ログインチケットの有効期限（秒）"""

    # === デバッグ設定 ===
    SAML_DEBUG_MODE: bool = False
    """SAMLデバッグモード - 詳細ログ出力"""

    SAML_SKIP_SSL_VERIFY: bool = False
    """SSL証明書検証スキップ (開発環境専用)"""

    SAML_IDP_METADATA_URL: Optional[str] = None
    """SAML IdP メタデータURL（オプション - 自動設定取得用）"""

    SAML_METADATA_CACHE_TTL_SECONDS: int = 3600
    """メタデータキャッシュの有効期限（秒）デフォルト: 1時間"""

    SAML_CERT_FETCH_STRATEGY: str = "auto"
    """
    証明書取得戦略:
    - 'auto': メタデータURL優先、失敗時は静的証明書にフォールバック（推奨）
    - 'metadata': メタデータURLのみ使用（動的取得専用）
    - 'static': 静的証明書のみ使用（レガシー環境）
    - 'hybrid': 両方を併用（マルチIdP環境）
    """

    SAML_METADATA_AUTO_REFRESH_ON_ERROR: bool = True
    """署名検証失敗時にメタデータを自動再取得するか"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    def get_cert_strategy(self) -> str:
        """証明書取得戦略を取得し、検証する"""
        valid_strategies = {"auto", "metadata", "static", "hybrid"}
        strategy = self.SAML_CERT_FETCH_STRATEGY.lower()

        if strategy not in valid_strategies:
            return "auto"  # デフォルトにフォールバック

        return strategy

    def should_use_metadata(self) -> bool:
        """メタデータ取得を使用すべきか判定"""
        strategy = self.get_cert_strategy()
        return strategy in {"auto", "metadata", "hybrid"} and bool(
            self.SAML_IDP_METADATA_URL
        )

    def should_use_static_cert(self) -> bool:
        """静的証明書を使用すべきか判定"""
        strategy = self.get_cert_strategy()
        return strategy in {"auto", "static", "hybrid"} and bool(
            self.SAML_IDP_X509_CERT
        )

    def get_allowed_domains(self) -> list[str]:
        """
        許可ドメインリストを取得

        Returns:
            許可ドメインのリスト。設定がない場合は空リスト
        """
        if not self.SAML_ALLOWED_DOMAINS:
            return []
        return [domain.strip() for domain in self.SAML_ALLOWED_DOMAINS.split(",")]

    def get_allowed_redirect_uris(self) -> list[str]:
        """リダイレクトURIの許可リストを取得"""
        if not self.SAML_ALLOWED_REDIRECT_URIS:
            return []
        return [
            uri.strip()
            for uri in self.SAML_ALLOWED_REDIRECT_URIS.split(",")
            if uri.strip()
        ]

    def resolve_redirect_uri(self, requested_uri: Optional[str]) -> str:
        """
        要求されたリダイレクトURIが許可されているか検証し、有効なURIを返す

        Args:
            requested_uri: フロントエンドから指定されたリダイレクトURI

        Returns:
            使用可能なリダイレクトURI。許可されていない場合はデフォルトにフォールバック
        """
        allowed_uris = set(self.get_allowed_redirect_uris())
        default_uri = self.SAML_DEFAULT_REDIRECT_URI or "/"

        if requested_uri and requested_uri in allowed_uris.union({default_uri}):
            return requested_uri

        if allowed_uris:
            return (
                default_uri if default_uri in allowed_uris else next(iter(allowed_uris))
            )

        return default_uri

    def is_domain_allowed(self, email: str) -> bool:
        """
        メールアドレスのドメインが許可されているかチェック

        Args:
            email: チェックするメールアドレス

        Returns:
            許可されている場合 True、そうでなければ False
        """
        allowed_domains = self.get_allowed_domains()
        if not allowed_domains:  # 設定がない場合は全許可
            return True

        domain = email.split("@")[-1] if "@" in email else ""
        return domain.lower() in [d.lower() for d in allowed_domains]

    def get_attribute_mapping(self) -> Dict[str, str]:
        """
        SAML属性マッピング設定を取得

        Returns:
            属性マッピング辞書。設定がない場合はデフォルト値
        """
        if self.SAML_ATTRIBUTE_MAPPING:
            try:
                import json

                return json.loads(self.SAML_ATTRIBUTE_MAPPING)
            except (json.JSONDecodeError, ImportError):
                pass

        # デフォルト属性マッピング
        return {
            "email": self.SAML_DEFAULT_ATTRIBUTE_EMAIL,
            "name": self.SAML_DEFAULT_ATTRIBUTE_NAME,
            "given_name": self.SAML_DEFAULT_ATTRIBUTE_GIVEN_NAME,
            "family_name": self.SAML_DEFAULT_ATTRIBUTE_SURNAME,
        }

    def get_saml_security_settings(self) -> Dict[str, Any]:
        """
        python3-saml用のセキュリティ設定を取得

        Returns:
            python3-saml セキュリティ設定辞書
        """
        return {
            "nameIdEncrypted": False,
            "authnRequestsSigned": self.SAML_SIGN_REQUESTS,
            "logoutRequestSigned": self.SAML_SIGN_REQUESTS,
            "logoutResponseSigned": self.SAML_SIGN_REQUESTS,
            "signMetadata": False,
            "wantAssertionsSigned": self.SAML_SIGN_ASSERTIONS,
            "wantNameId": True,
            "wantAssertionsEncrypted": self.SAML_ENCRYPT_ASSERTIONS,
            "wantNameIdEncrypted": False,
            "requestedAuthnContext": True,
            "signatureAlgorithm": self.SAML_SIGNATURE_ALGORITHM,
            "digestAlgorithm": self.SAML_DIGEST_ALGORITHM,
        }

    def get_saml_sp_settings(self) -> Dict[str, Any]:
        """
        python3-saml用のSP設定を取得

        Returns:
            python3-saml SP設定辞書
        """
        sp_settings = {
            "entityId": self.SAML_SP_ENTITY_ID,
            "assertionConsumerService": {
                "url": self.SAML_SP_ACS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "NameIDFormat": self.SAML_NAME_ID_FORMAT,
        }

        if self.SAML_SP_SLS_URL:
            sp_settings["singleLogoutService"] = {
                "url": self.SAML_SP_SLS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            }

        if self.SAML_SP_X509_CERT and self.SAML_SP_PRIVATE_KEY:
            sp_settings["x509cert"] = self.SAML_SP_X509_CERT
            sp_settings["privateKey"] = self.SAML_SP_PRIVATE_KEY

        return sp_settings

    def get_saml_idp_settings(self) -> Dict[str, Any]:
        """
        python3-saml用のIdP設定を取得

        Returns:
            python3-saml IdP設定辞書
        """
        idp_settings = {
            "entityId": self.SAML_IDP_ENTITY_ID,
            "singleSignOnService": {
                "url": self.SAML_IDP_SSO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": self.SAML_IDP_X509_CERT,
        }

        if self.SAML_IDP_SLS_URL:
            idp_settings["singleLogoutService"] = {
                "url": self.SAML_IDP_SLS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            }

        return idp_settings

    def validate_required_settings(self) -> bool:
        """
        必須設定値が設定されているかチェック

        Returns:
            全ての必須設定が設定されている場合 True
        """
        required_fields = [
            "SAML_SP_ENTITY_ID",
            "SAML_IDP_ENTITY_ID",
            "SAML_IDP_SSO_URL",
            "SAML_IDP_X509_CERT",
            "SAML_SP_ACS_URL",
            "SAML_RELAY_STATE_SIGNING_KEY",
        ]

        for field in required_fields:
            if not getattr(self, field):
                return False
        return True


# グローバルSAML設定インスタンス
saml_settings = SAMLSettings()


def get_saml_settings() -> SAMLSettings:
    """
    SAML設定インスタンスを取得

    依存性注入で使用するファクトリ関数

    Returns:
        SAMLSettings インスタンス
    """
    return saml_settings
