from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from typing import List, Optional, Union

class Settings(BaseSettings):
    # 既存の設定...
    # JWT Access Token有効期限（本番環境は 15-30 分を推奨）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Refresh Token有効期限（日数）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SERVER_NAME: str = "KOIKI Framework"
    SERVER_HOST: AnyHttpUrl = Field(default="http://localhost:8000")
    
    # アプリケーション名を追加
    APP_NAME: str = "KOIKI Framework"
    
    # BACKEND_CORS_ORIGINS is a comma-separated list of browser origins.
    BACKEND_CORS_ORIGINS: List[str] = []

    # API設定
    API_PREFIX: str = "/api/v1"  # API URLのプレフィックスを追加

    # ログ設定
    LOG_LEVEL: str = "INFO"  # デフォルトでINFOログレベルを設定
    LOG_FORMAT: str = "json"  # "json" または "console"
    LOG_TIMEZONE: str = "UTC"  # ログの日時タイムゾーン (例: "UTC", "Asia/Tokyo")
    APP_ENV: str = "development"  # "development", "testing", "production"
    DEBUG: bool = True  # デバッグモードの有効/無効
    
    # データベース設定 - PostgreSQL専用
    DATABASE_URL: Optional[str] = None  # PostgreSQL接続文字列
    
    # レートリミット設定
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "10/minute"
    RATE_LIMIT_STRATEGY: str = "fixed-window"
    
    # データベース接続プール設定
    DB_POOL_SIZE: int = 5  # 接続プールサイズ
    DB_MAX_OVERFLOW: int = 10  # 最大オーバーフロー
    DB_POOL_TIMEOUT: int = 30       # プール枯渇時に待つ秒数 (SQLAlchemy デフォルト 30s)
    DB_ECHO: bool = False  # SQLログ出力

    PROJECT_NAME: str = "KOIKI Framework"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: Optional[str] = None    # Redis設定（オプション）
    REDIS_ENABLED: bool = False  # Redisを使用するかどうか
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    
    # JWT関連設定
    JWT_SECRET: str = "jwt_secret_development_only"
    JWT_ALGORITHM: str = "HS256"

    # Browser Cookie authentication settings
    AUTH_ACCESS_COOKIE_NAME: str = "koiki_access_token"
    AUTH_REFRESH_COOKIE_NAME: str = "koiki_refresh_token"
    AUTH_CSRF_COOKIE_NAME: str = "koiki_csrf_token"
    AUTH_CSRF_HEADER_NAME: str = "x-csrf-token"
    AUTH_CSRF_SECRET: str = "csrf_secret_development_only"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_COOKIE_DOMAIN: Optional[str] = None
    AUTH_COOKIE_PATH: str = "/"
    AUTH_REFRESH_COOKIE_PATH: Optional[str] = None
    AUTH_CSRF_COOKIE_MAX_AGE_SECONDS: int = 24 * 60 * 60
    
    # レート制限設定
    RATE_LIMIT_PER_SECOND: int = 10

    @field_validator("AUTH_COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, v: str) -> str:
        normalized = v.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip().rstrip("/") for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [i.strip().rstrip("/") for i in v if i.strip()]
        elif isinstance(v, str):
            return v
        raise ValueError(v)

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        if self.DATABASE_URL:
            return self

        # PostgreSQLのURLを構築
        self.DATABASE_URL = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # アプリケーション初期化時の追加設定
        # Redis URL がない場合は構築する
        if not self.REDIS_URL and self.REDIS_HOST:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

# グローバル設定オブジェクト
settings = Settings()
