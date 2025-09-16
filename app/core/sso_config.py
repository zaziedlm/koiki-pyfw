# app/core/sso_config.py
"""
SSO (Single Sign-On) 設定管理

OpenID Connect (OIDC) による外部認証サービスとの連携に必要な
設定値を管理します。環境変数から読み込み、適切なデフォルト値を提供。
"""
from typing import Optional

from pydantic_settings import BaseSettings


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
    
    # === オプション設定 ===
    SSO_AUTO_CREATE_USERS: bool = True
    """初回SSO ログイン時の自動ユーザー作成フラグ"""
    
    SSO_DEFAULT_PROVIDER: str = "oidc"
    """デフォルトSSOプロバイダー名"""
    
    SSO_TOKEN_CACHE_TTL: int = 300
    """JWKSトークン検証キャッシュTTL (秒)"""
    
    SSO_ALLOWED_DOMAINS: Optional[str] = None
    """許可ドメインリスト (カンマ区切り)。Noneの場合は全ドメイン許可"""
    SSO_ALLOWED_AUDIENCES: Optional[str] = None
    """許可する aud 値をカンマ区切りで列挙"""

    
    SSO_REQUIRE_EMAIL_VERIFIED: bool = True
    """メール検証済み要求フラグ"""
    
    SSO_USER_INFO_ENDPOINT: Optional[str] = None
    """ユーザー情報取得エンドポイント (オプション)"""
    SSO_ALLOW_SUB_UPDATE: bool = False
    """IdP 側で subject が変わった場合にローカル連携を更新するか"""

    
    SSO_INTROSPECTION_ENABLED: bool = False
    """RFC 7662 のイントロスペクションでアクセストークンを検証するかどうか"""

    SSO_INTROSPECTION_ENDPOINT: Optional[str] = None
    """OAuth2 イントロスペクション エンドポイントの URL"""

    SSO_INTROSPECTION_AUTH_MODE: str = "basic"
    """イントロスペクション時の認証方式 (basic / bearer / none)"""

    SSO_INTROSPECTION_TOKEN: Optional[str] = None
    """イントロスペクションで Bearer 認証に用いるトークン"""

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
    
    # === デバッグ設定 ===
    SSO_DEBUG_MODE: bool = False
    """SSOデバッグモード - 詳細ログ出力"""
    
    SSO_SKIP_SSL_VERIFY: bool = False
    """SSL証明書検証スキップ (開発環境専用)"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_allowed_audiences(self) -> list[str]:
        """許可された aud のリストを取得する。"""
        if not self.SSO_ALLOWED_AUDIENCES:
            return []
        return [aud.strip() for aud in self.SSO_ALLOWED_AUDIENCES.split(',') if aud.strip()]

    def get_allowed_domains(self) -> list[str]:
        """許可ドメインのリストを取得する。"""
        if not self.SSO_ALLOWED_DOMAINS:
            return []
        return [domain.strip() for domain in self.SSO_ALLOWED_DOMAINS.split(',') if domain.strip()]

    def is_domain_allowed(self, email: str) -> bool:
        """メールアドレスが許可ドメインに含まれるか判定する。"""
        allowed_domains = self.get_allowed_domains()
        if not allowed_domains:
            return True

        domain = email.split('@')[-1] if '@' in email else ''
        return domain.lower() in [d.lower() for d in allowed_domains]

    def validate_required_settings(self) -> bool:
        """必須設定が満たされているかを検証する。"""
        base_required = [
            'SSO_CLIENT_ID',
            'SSO_ISSUER_URL',
        ]

        for field in base_required:
            if not getattr(self, field):
                return False

        if self.SSO_INTROSPECTION_ENABLED:
            if not self.SSO_INTROSPECTION_ENDPOINT:
                return False

            mode = (self.SSO_INTROSPECTION_AUTH_MODE or 'basic').lower()
            if mode == 'basic':
                return bool(self.SSO_CLIENT_SECRET)
            if mode == 'bearer':
                return bool(self.SSO_INTROSPECTION_TOKEN)
            return True

        return bool(self.SSO_JWKS_URI)




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