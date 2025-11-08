from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field, PostgresDsn, validator
from typing import List, Optional, Union, Dict, Any

class Settings(BaseSettings):
    # 既存の設定...
    # JWT Access Token有効期限（開発環境：60分、本番環境：15分推奨）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Refresh Token有効期限（日数）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SERVER_NAME: str = "KOIKI Framework"
    SERVER_HOST: AnyHttpUrl = Field(default="http://localhost:8000")
    
    # アプリケーション名を追加
    APP_NAME: str = "KOIKI Framework"
    
    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # API設定
    API_PREFIX: str = "/api/v1"  # API URLのプレフィックスを追加

    # ログ設定
    LOG_LEVEL: str = "INFO"  # デフォルトでINFOログレベルを設定
    LOG_FORMAT: str = "json"  # "json" または "console"    # 環境設定
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
    
    # レート制限設定
    RATE_LIMIT_PER_SECOND: int = 10

    # CSRF tokens
    CSRF_SECRET: str = "csrf_secret_development_only"
    CSRF_TOKEN_TTL_SECONDS: int = 3600

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
            
        # PostgreSQLのURLを構築
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT", 5432)
        db = values.get("POSTGRES_DB", "")
        
        # PostgreSQL接続URI
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # アプリケーション初期化時の追加設定
        # Redis URL がない場合は構築する
        if not self.REDIS_URL and self.REDIS_HOST:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

# グローバル設定オブジェクト
settings = Settings()
