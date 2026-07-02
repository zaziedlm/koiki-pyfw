import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
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
from libkoiki.core.browser_session import BrowserSessionCSRFMiddleware
from libkoiki.core.config import settings
from libkoiki.core.error_handlers import setup_exception_handlers
from libkoiki.core.logging import get_logger, setup_logging
from libkoiki.core.middleware import (
    AccessLogMiddleware,
    AuditLogMiddleware,
    RequestContextLogMiddleware,
    SecurityHeadersMiddleware,
)
from libkoiki.core.monitoring import setup_monitoring
from libkoiki.db.session import AsyncSessionFactory, connect_db, disconnect_db
from libkoiki.events.handlers import (
    EventHandler,
    user_created_handler,
)
from libkoiki.events.publisher import EventPublisher

# TODO : Celeryひとまずコメントアウト
# from libkoiki.tasks.celery_app import celery_app # Celery App インスタンス

# ロギング設定を最初に呼び出す
setup_logging()
logger = get_logger(__name__)

# SAML認証フロークリーンアップ用
from koiki_ref_app.repositories.saml_auth_flow_repository import (
    SamlAuthFlowRepository,
)
from koiki_ref_app.bootstrap import bootstrap_orm

_cleanup_task: Optional[asyncio.Task] = None

CLEANUP_INTERVAL_SECONDS = 300  # 5分間隔


async def _periodic_saml_flow_cleanup() -> None:
    """期限切れSAML認証フローを定期的にクリーンアップするバックグラウンドタスク"""
    repo = SamlAuthFlowRepository()
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            if AsyncSessionFactory is None:
                continue
            async with AsyncSessionFactory() as session:
                count = await repo.cleanup_expired_flows(session)
                await session.commit()
                if count > 0:
                    logger.info("Periodic SAML flow cleanup completed", cleaned=count)
        except asyncio.CancelledError:
            logger.info("SAML flow cleanup task cancelled")
            break
        except Exception:
            logger.exception("Error in periodic SAML flow cleanup")


# --- Application Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application startup sequence initiated.")
    app.state.redis_pool = None
    app.state.redis = None
    app.state.event_publisher = None
    app.state.event_handler = None
    app.state.limiter = None
    await connect_db()

    # --- データベーススキーマは Alembic マイグレーションで管理 ---
    logger.info(
        "Database connection established. Tables should be managed by Alembic migrations."
    )
    # --- Redis 接続プールとクライアント初期化 ---
    if settings.REDIS_ENABLED and REDIS_AVAILABLE and settings.REDIS_URL:
        try:
            logger.info(
                "Initializing Redis connection pool...", redis_url=settings.REDIS_URL
            )
            app.state.redis_pool = ConnectionPool.from_url(
                settings.REDIS_URL, decode_responses=True, max_connections=10
            )
            app.state.redis = Redis(connection_pool=app.state.redis_pool)
            await app.state.redis.ping()
            logger.info("Redis connection successful.")
            app.state.event_publisher = EventPublisher(redis_client=app.state.redis)
            logger.info("Event publisher initialized.")
            logger.info("Event handling is disabled in initial version.")
        except Exception as e:
            logger.error(
                f"Failed to connect to or initialize Redis components: {e}",
                exc_info=True,
            )
            app.state.redis = None
            app.state.event_publisher = None
            app.state.event_handler = None
    else:
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis package is not installed. Using dummy implementations for Redis-dependent features."
            )
            app.state.redis = Redis()
            app.state.redis_pool = None
            app.state.event_publisher = EventPublisher(redis_client=app.state.redis)
            logger.info("Dummy event publisher initialized.")
            app.state.event_handler = None
        else:
            logger.warning(
                "Redis URL not configured. Redis-dependent features (Events, Rate Limiting Strategy, Caching) might be disabled or limited."
            )
    # --- レートリミッター初期化 ---
    redis_storage_uri = (
        settings.REDIS_URL if app.state.redis and REDIS_AVAILABLE else None
    )
    storage_options = {"decode_responses": True} if redis_storage_uri else {}

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
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info(
        "Rate limiter initialized.",
        enabled=settings.RATE_LIMIT_ENABLED,
        strategy=settings.RATE_LIMIT_STRATEGY,
    )

    logger.info("Application startup sequence completed.")

    global _cleanup_task
    _cleanup_task = asyncio.create_task(_periodic_saml_flow_cleanup())
    logger.info(
        "SAML flow cleanup task started",
        interval_seconds=CLEANUP_INTERVAL_SECONDS,
    )

    yield
    logger.info("Application shutdown sequence initiated.")

    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("SAML flow cleanup task stopped")

    if app.state.redis and REDIS_AVAILABLE:
        logger.info("Closing Redis connection.")
        await app.state.redis.close()
    if app.state.redis_pool and REDIS_AVAILABLE:
        logger.info("Disposing Redis connection pool.")
        await app.state.redis_pool.disconnect()

    await disconnect_db()

    logger.info("Application shutdown sequence completed.")


def create_app() -> FastAPI:
    """Create the reference application instance."""
    bootstrap_orm()

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        version="0.7.1",
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware enabled.", origins=settings.BACKEND_CORS_ORIGINS)

    # Keep Cookie-authenticated browser mutations behind an explicit CSRF gate.
    app.add_middleware(BrowserSessionCSRFMiddleware)
    logger.info("Browser session CSRF middleware enabled.")

    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled.")

    app.add_middleware(AuditLogMiddleware)
    logger.info("Audit log middleware enabled.")

    app.add_middleware(RequestContextLogMiddleware)
    logger.info("Request context log middleware enabled.")

    setup_exception_handlers(app)

    from koiki_ref_app.api.v1.router import router as app_api_router

    app.include_router(app_api_router, prefix=settings.API_PREFIX)
    logger.info("Application API router included.", prefix=settings.API_PREFIX)

    app.include_router(api_router_v1, prefix=settings.API_PREFIX)
    logger.info("libkoiki API router v1 included.", prefix=settings.API_PREFIX)

    @app.get("/health", tags=["Health Check"])
    async def health_check(request: Request):
        """システムヘルスチェック"""
        from datetime import datetime, timezone

        logger.debug("Health check endpoint called.")
        return {
            "status": "healthy",
            "service": "koiki-framework",
            "version": "0.7.1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/", tags=["Service Info"])
    async def root(request: Request):
        """API情報とドキュメントリンク"""
        logger.debug("Root endpoint called.")
        return {
            "service": "KOIKI Framework API",
            "version": "0.7.1",
            "docs": "/docs",
            "health": "/health",
        }

    return app
