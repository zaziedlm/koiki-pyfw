# main.py
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware  # オプション: グローバル制限用
from slowapi.util import get_remote_address

# Redis依存の条件付きインポート
try:
    from redis.asyncio import ConnectionPool, Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    # Redis非依存の代替実装やスタブを提供
    class DummyRedis:
        """Redis APIのスタブ実装"""

        async def ping(self):
            return True

        async def publish(self, *args, **kwargs):
            return 0

        async def close(self):
            pass

    class DummyConnectionPool:
        """Redis ConnectionPoolのスタブ実装"""

        @classmethod
        def from_url(cls, *args, **kwargs):
            return cls()

        async def disconnect(self):
            pass

    Redis = DummyRedis
    ConnectionPool = DummyConnectionPool

from libkoiki.api.v1.router import api_router as api_router_v1
from libkoiki.core.config import settings
from libkoiki.core.error_handlers import setup_exception_handlers
from libkoiki.core.logging import get_logger, setup_logging
from libkoiki.core.middleware import (  # AccessLogMiddlewareはオプション
    AccessLogMiddleware,
    AuditLogMiddleware,
    SecurityHeadersMiddleware,
)
from libkoiki.core.monitoring import setup_monitoring
from libkoiki.db.session import connect_db, disconnect_db
from libkoiki.events.handlers import (  # サンプルハンドラ
    EventHandler,
    user_created_handler,
)
from libkoiki.events.publisher import EventPublisher

# TODO : Celeryひとまずコメントアウト
# from libkoiki.tasks.celery_app import celery_app # Celery App インスタンス

# ロギング設定を最初に呼び出す
setup_logging()
logger = get_logger(__name__)


# --- Application Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application startup sequence initiated.")
    app.state.redis_pool = None
    app.state.redis = None
    app.state.event_publisher = None
    app.state.event_handler = None
    app.state.limiter = None  # --- データベース接続確認 ---
    await connect_db()

    # --- データベーススキーマは Alembic マイグレーションで管理 ---
    # PostgreSQL環境ではAlembicを使用してスキーマを管理するのが望ましいです
    logger.info(
        "Database connection established. Tables should be managed by Alembic migrations."
    )  # --- Redis 接続プールとクライアント初期化 ---
    # シンプル版では Redis は使用しない
    if settings.REDIS_ENABLED and REDIS_AVAILABLE and settings.REDIS_URL:
        try:
            logger.info(
                "Initializing Redis connection pool...", redis_url=settings.REDIS_URL
            )
            app.state.redis_pool = ConnectionPool.from_url(
                settings.REDIS_URL, decode_responses=True, max_connections=10
            )
            app.state.redis = Redis(connection_pool=app.state.redis_pool)
            # 接続テスト
            await app.state.redis.ping()
            logger.info("Redis connection successful.")

            # --- イベントパブリッシャー初期化 (Redisが必要) ---
            app.state.event_publisher = EventPublisher(redis_client=app.state.redis)
            logger.info("Event publisher initialized.")

            # --- イベントハンドラー初期化とリスニング開始 (Redisが必要) ---
            # 初期版では非同期イベント配信を無効化
            logger.info("Event handling is disabled in initial version.")
        except Exception as e:
            logger.error(
                f"Failed to connect to or initialize Redis components: {e}",
                exc_info=True,
            )
            # Redis接続失敗時の処理 (必要なら起動中止など)
            app.state.redis = None  # Redisを使えないことを示す
            app.state.event_publisher = None
            app.state.event_handler = None
    else:
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis package is not installed. Using dummy implementations for Redis-dependent features."
            )
            # ダミー実装を提供
            app.state.redis = Redis()  # DummyRedis インスタンス
            app.state.redis_pool = None
            # ダミーのEventPublisherとEventHandlerを初期化
            app.state.event_publisher = EventPublisher(redis_client=app.state.redis)
            logger.info("Dummy event publisher initialized.")
            # イベントハンドラーはダミー実装でリスニングしないため不要
            app.state.event_handler = None
        else:
            logger.warning(
                "Redis URL not configured. Redis-dependent features (Events, Rate Limiting Strategy, Caching) might be disabled or limited."
            )
    # --- レートリミッター初期化 ---
    # storage_uri は Redis が利用可能な場合のみ設定
    redis_storage_uri = (
        settings.REDIS_URL if app.state.redis and REDIS_AVAILABLE else None
    )
    storage_options = (
        {"decode_responses": True} if redis_storage_uri else {}
    )  # Redis使用時のオプション

    # REDIS_AVAILABLEがFalseの場合、戦略をredisからfixedwindowに変更
    strategy = settings.RATE_LIMIT_STRATEGY
    if not REDIS_AVAILABLE and strategy == "redis":
        strategy = "fixed-window"
        logger.warning(
            "Changed rate limit strategy from 'redis' to 'fixed-window' due to Redis unavailability"
        )

    limiter = Limiter(
        key_func=get_remote_address,
        enabled=settings.RATE_LIMIT_ENABLED,
        default_limits=[settings.RATE_LIMIT_DEFAULT]
        if settings.RATE_LIMIT_ENABLED
        else [],
        strategy=strategy,
        storage_uri=redis_storage_uri,
        storage_options=storage_options,
    )
    app.state.limiter = limiter
    # slowapi のデフォルトハンドラを使用（カスタムする場合は error_handlers で設定）
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    # オプション: グローバル制限をミドルウェアでかける場合
    # app.add_middleware(SlowAPIMiddleware) # limiterインスタンスは自動でstateから取得される
    logger.info(
        "Rate limiter initialized.",
        enabled=settings.RATE_LIMIT_ENABLED,
        strategy=settings.RATE_LIMIT_STRATEGY,
    )

    logger.info("Application startup sequence completed.")
    yield  # アプリケーション実行
    logger.info(
        "Application shutdown sequence initiated."
    )  # --- イベントハンドラー停止 ---
    # 初期版では無効化
    # if app.state.event_handler:
    #     logger.info("Stopping event handler listening.")
    #     await app.state.event_handler.stop_listening()

    # --- Redis 接続プール切断 ---
    if app.state.redis and REDIS_AVAILABLE:
        logger.info("Closing Redis connection.")
        await app.state.redis.close()  # クライアントを閉じる
    if app.state.redis_pool and REDIS_AVAILABLE:
        logger.info("Disposing Redis connection pool.")
        await app.state.redis_pool.disconnect()  # プールを破棄

    # --- データベース接続プール切断 ---
    await disconnect_db()

    logger.info("Application shutdown sequence completed.")


# --- FastAPI アプリケーションインスタンス ---
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.6.0",  # フレームワークバージョン
    openapi_url="/openapi.json"
    if settings.APP_ENV != "production"
    else None,  # 本番では無効化も
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,  # アプリケーションライフサイクル管理
)

# --- ミドルウェア設定 ---
# 注意: ミドルウェアの順序は重要。外側から内側へ処理される。
# 1. CORS (最初に適用することが多い)
# 開発環境では寛容なCORS設定（プロキシリダイレクト問題を回避）
if settings.APP_ENV == "development":
    # 開発環境用の寛容なCORS設定
    development_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=development_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware enabled for development", origins=development_origins)
elif settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware enabled.", origins=settings.BACKEND_CORS_ORIGINS)

# 2. セキュリティヘッダ
app.add_middleware(SecurityHeadersMiddleware)
logger.info("Security headers middleware enabled.")

# 3. 監査ログ (リクエスト/レスポンス情報を記録)
app.add_middleware(AuditLogMiddleware)
logger.info("Audit log middleware enabled.")

# 4. オプション: アクセスログ (structlogでuvicornアクセスログを処理する場合は不要なことも)
# app.add_middleware(AccessLogMiddleware)
# logger.info("Access log middleware enabled.")

# 5. オプション: レートリミット (グローバル制限)
# エンドポイントごとの制限が主なら不要。ミドルウェアを使う場合はハンドラ登録より先に。
# app.add_middleware(SlowAPIMiddleware)

# --- 例外ハンドラー設定 ---
setup_exception_handlers(app)

# --- Prometheus モニタリング設定 ---
# setup_monitoring(app) # 必要に応じて有効化

# アプリケーション固有API
from app.api.v1.router import router as app_api_router

app.include_router(app_api_router, prefix=settings.API_PREFIX)
logger.info("Application API router included.", prefix=settings.API_PREFIX)

# --- API ルーター設定 ---
# libkoikiの標準API
app.include_router(api_router_v1, prefix=settings.API_PREFIX)
logger.info("libkoiki API router v1 included.", prefix=settings.API_PREFIX)


# --- ヘルスチェックエンドポイント ---
@app.get("/health", tags=["Health Check"])
async def health_check(request: Request):
    """システムヘルスチェック"""
    from datetime import datetime

    logger.debug("Health check endpoint called.")
    return {
        "status": "healthy",
        "service": "koiki-framework",
        "version": "0.6.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# --- ルートエンドポイント (API情報) ---
@app.get("/", tags=["Service Info"])
async def root(request: Request):
    """API情報とドキュメントリンク"""
    logger.debug("Root endpoint called.")
    return {
        "service": "KOIKI Framework API",
        "version": "0.6.0",
        "docs": "/docs",
        "health": "/health",
    }


# Uvicorn で実行する場合: uvicorn main:app --reload
