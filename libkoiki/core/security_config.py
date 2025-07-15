# src/core/security_config.py
"""
セキュリティ関連の設定値を集約管理
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginSecurityConfig(BaseModel):
    """ログインセキュリティ関連の設定"""
    
    # ログイン試行制限
    max_attempts_per_email: int = Field(default=5, description="メールアドレス単位の最大失敗試行数")
    max_attempts_per_ip: int = Field(default=10, description="IP単位の最大失敗試行数")
    lockout_duration_minutes: int = Field(default=15, description="ロックアウト期間（分）")
    
    # 段階的遅延
    progressive_delay_base: int = Field(default=2, description="段階的遅延のベース時間（秒）")
    max_progressive_delay: int = Field(default=30, description="最大段階的遅延時間（秒）")
    
    # タイミング攻撃対策
    min_response_time: float = Field(default=0.1, description="最小応答時間（秒）")
    
    # レート制限
    login_rate_limit: str = Field(default="10/minute", description="ログインのレート制限")
    register_rate_limit: str = Field(default="5/minute", description="登録のレート制限")
    
    # セッション設定
    access_token_expire_minutes: int = Field(default=30, description="アクセストークン有効期限（分）")
    refresh_token_expire_days: int = Field(default=7, description="リフレッシュトークン有効期限（日）")
    
    # ログ保存設定
    login_attempt_retention_days: int = Field(default=30, description="ログイン試行履歴保存期間（日）")
    
    # パスワードポリシー
    password_min_length: int = Field(default=8, description="パスワード最小長")
    password_require_uppercase: bool = Field(default=True, description="大文字必須")
    password_require_lowercase: bool = Field(default=True, description="小文字必須")
    password_require_digit: bool = Field(default=True, description="数字必須")
    password_require_symbol: bool = Field(default=True, description="記号必須")


class SecurityConfig(BaseModel):
    """セキュリティ全般の設定"""
    
    # ログインセキュリティ設定
    login_security: LoginSecurityConfig = Field(default_factory=LoginSecurityConfig)
    
    # セキュリティヘッダー
    enable_security_headers: bool = Field(default=True, description="セキュリティヘッダーを有効化")
    enable_cors: bool = Field(default=True, description="CORSを有効化")
    
    # 監査ログ
    enable_audit_logging: bool = Field(default=True, description="監査ログを有効化")
    audit_log_retention_days: int = Field(default=90, description="監査ログ保存期間（日）")
    
    # 暗号化
    jwt_algorithm: str = Field(default="HS256", description="JWT署名アルゴリズム")
    password_hash_rounds: int = Field(default=12, description="パスワードハッシュのラウンド数")
    
    # IP制限
    enable_ip_whitelist: bool = Field(default=False, description="IP許可リストを有効化")
    allowed_ips: list[str] = Field(default_factory=list, description="許可されたIPアドレス")
    blocked_ips: list[str] = Field(default_factory=list, description="ブロックされたIPアドレス")
    
    # デバイス管理
    enable_device_tracking: bool = Field(default=True, description="デバイス追跡を有効化")
    max_devices_per_user: int = Field(default=5, description="ユーザーあたりの最大デバイス数")
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


# グローバル設定インスタンス（環境変数から自動読み込み）
security_config = SecurityConfig()


def get_login_security_config() -> LoginSecurityConfig:
    """ログインセキュリティ設定を取得"""
    return security_config.login_security


def get_security_config() -> SecurityConfig:
    """セキュリティ設定全体を取得"""
    return security_config


def update_config(**kwargs) -> None:
    """設定値を動的に更新（テスト用）"""
    global security_config
    current_dict = security_config.dict()
    current_dict.update(kwargs)
    security_config = SecurityConfig(**current_dict)