# app/core/sso_config.py
"""
SSO (Single Sign-On) 設定管理

OpenID Connect (OIDC) による外部認証サービスとの連携に必要な
設定値を管理します。環境変数から読み込み、適切なデフォルト値を提供。
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class SSOSettings(BaseSettings):
    """
    SSO認証設定クラス
    
    OpenID Connect プロバイダーとの連携に必要な設定値を定義
    環境変数 (.env ファイル) から設定を読み込む
    """
    
    # === 必須設定 ===
    SSO_CLIENT_ID: str = ""
    """OIDCクライアントID - SSOプロバイダーから発行される"""
    
    SSO_CLIENT_SECRET: str = ""
    """OIDCクライアントシークレット - SSOプロバイダーから発行される"""
    
    SSO_ISSUER_URL: str = ""
    """OIDC発行者URL - SSOプロバイダーのベースURL"""
    
    SSO_JWKS_URI: str = ""
    """JWKS (JSON Web Key Set) URI - トークン署名検証用公開鍵取得先"""

    SSO_TOKEN_ENDPOINT: str = ""
    """OIDCトークンエンドポイント - authorization code の交換に使用"""

    SSO_AUTHORIZATION_ENDPOINT: str = ""
    """OIDC認可エンドポイント - ブラウザからのリダイレクト先"""
    
    # === オプション設定 ===
    SSO_AUTO_CREATE_USERS: bool = True
    """初回SSO ログイン時の自動ユーザー作成フラグ"""
    
    SSO_DEFAULT_PROVIDER: str = "oidc"
    """デフォルトSSOプロバイダー名"""
    
    SSO_TOKEN_CACHE_TTL: int = 300
    """JWKSトークン検証キャッシュTTL (秒)"""
    
    SSO_ALLOWED_DOMAINS: Optional[str] = None
    """許可ドメインリスト (カンマ区切り)。Noneの場合は全ドメイン許可"""
    
    SSO_REQUIRE_EMAIL_VERIFIED: bool = True
    """メール検証済み要求フラグ"""

    SSO_USER_INFO_ENDPOINT: Optional[str] = None
    """ユーザー情報取得エンドポイント (オプション)"""

    SSO_DEFAULT_SCOPES: str = "openid email profile"
    """認可リクエストに付与するスコープ (スペース区切り)"""

    SSO_DEFAULT_REDIRECT_URI: Optional[str] = None
    """認可リクエストでデフォルト使用するredirect_uri"""

    SSO_ALLOWED_REDIRECT_URIS: Optional[str] = None
    """許可されたredirect_uriのリスト (カンマ区切り)"""
    
    # === セキュリティ設定 ===
    SSO_AUDIENCE_VALIDATION: bool = True
    """JWTオーディエンス検証の有効化"""
    
    SSO_ISSUER_VALIDATION: bool = True
    """JWT発行者検証の有効化"""
    
    SSO_SIGNATURE_VALIDATION: bool = True
    """JWT署名検証の有効化"""

    SSO_EXPIRY_VALIDATION: bool = True
    """JWT有効期限検証の有効化"""

    SSO_CLOCK_SKEW_SECONDS: int = 30
    """JWT時刻ずれ許容範囲 (秒)"""

    SSO_ALLOWED_ALGORITHMS: str = "RS256"
    """受け入れる署名アルゴリズム（カンマ区切り）"""

    SSO_EXPECTED_AZP: Optional[str] = None
    """複数audience時に検証するauthorized party（未設定時はclient_idを利用）"""

    # === デバッグ設定 ===
    SSO_DEBUG_MODE: bool = False
    """SSOデバッグモード - 詳細ログ出力"""
    
    SSO_SKIP_SSL_VERIFY: bool = False
    """SSL証明書検証スキップ (開発環境専用)"""

    SSO_STATE_SIGNING_KEY: str = ""
    """state検証用のHMACシークレット（前段で生成したstate tokenの検証に使用）"""

    SSO_STATE_TTL_SECONDS: int = 600
    """state token の許容有効期限 (秒)"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )
        
    def get_allowed_domains(self) -> list[str]:
        """
        許可ドメインリストを取得
        
        Returns:
            許可ドメインのリスト。設定がない場合は空リスト
        """
        if not self.SSO_ALLOWED_DOMAINS:
            return []
        return [domain.strip() for domain in self.SSO_ALLOWED_DOMAINS.split(",")]
    
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

    def get_allowed_algorithms(self) -> list[str]:
        """受け入れるJWTアルゴリズム一覧を取得"""
        if not self.SSO_ALLOWED_ALGORITHMS:
            return []
        return [alg.strip() for alg in self.SSO_ALLOWED_ALGORITHMS.split(",") if alg.strip()]

    def get_expected_azp(self) -> str:
        """azp検証時に使用する期待値を取得"""
        return self.SSO_EXPECTED_AZP or self.SSO_CLIENT_ID

    def get_scopes(self) -> str:
        """認可リクエストに付与するスコープ文字列を取得"""
        scopes = self.SSO_DEFAULT_SCOPES.strip()
        return scopes or "openid"

    def get_allowed_redirect_uris(self) -> list[str]:
        """許可されたredirect_uriリストを返す"""
        if not self.SSO_ALLOWED_REDIRECT_URIS:
            return []
        return [uri.strip() for uri in self.SSO_ALLOWED_REDIRECT_URIS.split(",") if uri.strip()]

    def get_default_redirect_uri(self) -> Optional[str]:
        """デフォルトで使用するredirect_uriを返す"""
        if self.SSO_DEFAULT_REDIRECT_URI:
            return self.SSO_DEFAULT_REDIRECT_URI
        allowed = self.get_allowed_redirect_uris()
        return allowed[0] if allowed else None

    def is_redirect_uri_allowed(self, redirect_uri: str) -> bool:
        """指定されたredirect_uriが許可リストに含まれるか検証"""
        allowed = self.get_allowed_redirect_uris()
        if not allowed:
            return True
        return redirect_uri in allowed

    def validate_required_settings(self) -> bool:
        """
        必須設定値が設定されているかチェック

        Returns:
            全ての必須設定が設定されている場合 True
        """
        required_fields = [
            "SSO_CLIENT_ID",
            "SSO_CLIENT_SECRET", 
            "SSO_ISSUER_URL",
            "SSO_JWKS_URI",
            "SSO_TOKEN_ENDPOINT",
            "SSO_AUTHORIZATION_ENDPOINT",
            "SSO_STATE_SIGNING_KEY",
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                return False
        return True


# グローバルSSO設定インスタンス
sso_settings = SSOSettings()


def get_sso_settings() -> SSOSettings:
    """
    SSO設定インスタンスを取得
    
    依存性注入で使用するファクトリ関数
    
    Returns:
        SSOSettings インスタンス
    """
    return sso_settings
