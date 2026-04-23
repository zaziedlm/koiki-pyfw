# 共通フィクスチャ設定（例: テストDB, クライアント）
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LIBKOIKI_SRC = os.path.join(REPO_ROOT, 'components', 'libkoiki', 'src')
KOIKI_REF_APP_SRC = os.path.join(REPO_ROOT, 'components', 'koiki_ref_app', 'src')

if LIBKOIKI_SRC not in sys.path:
    sys.path.insert(0, LIBKOIKI_SRC)
if KOIKI_REF_APP_SRC not in sys.path:
    sys.path.insert(1, KOIKI_REF_APP_SRC)
if REPO_ROOT not in sys.path:
    sys.path.insert(2, REPO_ROOT)

os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["REDIS_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"


@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループを作成"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """テスト用設定"""
    from libkoiki.core.config import Settings

    return Settings(
        APP_ENV="testing",
        DEBUG=True,
        REDIS_ENABLED=False,
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """テスト用データベースエンジン"""
    from koiki_ref_app.bootstrap import bootstrap_orm
    from libkoiki.db.base import Base
    import libkoiki.models  # noqa: F401
    import koiki_ref_app.models  # noqa: F401

    bootstrap_orm()

    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        poolclass=None,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッション - @transactionalデコレータと協調"""
    from libkoiki.db.base import Base

    table_names = [table.name for table in Base.metadata.sorted_tables]
    if table_names:
        truncate_sql = "TRUNCATE TABLE " + ", ".join(table_names) + " RESTART IDENTITY CASCADE"
        async with test_engine.begin() as conn:
            await conn.execute(text(truncate_sql))

    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
        # @transactionalデコレータがトランザクションを管理するため、
        # ここでは明示的にロールバックしない


@pytest.fixture
def test_client(test_engine):
    """テスト用FastAPIクライアント"""
    from koiki_ref_app.asgi import app
    from libkoiki.core.rate_limiter import limiter as shared_limiter
    from libkoiki.db.session import get_db
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    previous_shared_enabled = shared_limiter.enabled
    shared_limiter.enabled = False

    with TestClient(app) as client:
        if getattr(app.state, "limiter", None) is not None:
            app.state.limiter.enabled = False
        yield client

    shared_limiter.enabled = previous_shared_enabled
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """モック用データベースセッション"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.scalars = AsyncMock()
    session.scalar = AsyncMock()
    return session


@pytest_asyncio.fixture
async def test_repositories(test_db_session):
    """テスト用リポジトリ"""
    from libkoiki.repositories.user_repository import UserRepository
    from libkoiki.repositories.refresh_token_repository import RefreshTokenRepository
    from libkoiki.repositories.login_attempt_repository import LoginAttemptRepository
    
    # リポジトリのインスタンス作成
    user_repo = UserRepository()
    refresh_token_repo = RefreshTokenRepository()
    login_attempt_repo = LoginAttemptRepository()
    
    # データベースセッションを設定
    user_repo.set_session(test_db_session)
    refresh_token_repo.set_session(test_db_session)
    login_attempt_repo.set_session(test_db_session)
    
    return {
        "user_repo": user_repo,
        "refresh_token_repo": refresh_token_repo,
        "login_attempt_repo": login_attempt_repo,
    }


@pytest_asyncio.fixture
async def test_services(test_repositories):
    """テスト用サービス"""
    from libkoiki.services.user_service import UserService
    from libkoiki.services.auth_service import AuthService
    from libkoiki.services.login_security_service import LoginSecurityService
    
    # サービスのインスタンス作成
    user_service = UserService(
        repository=test_repositories["user_repo"],
        event_publisher=None  # テストではイベントパブリッシャーを無効化
    )
    
    auth_service = AuthService(
        refresh_token_repo=test_repositories["refresh_token_repo"],
        user_repo=test_repositories["user_repo"]
    )
    
    login_security_service = LoginSecurityService(
        login_attempt_repository=test_repositories["login_attempt_repo"]
    )
    
    return {
        "user_service": user_service,
        "auth_service": auth_service,
        "login_security_service": login_security_service,
    }


# テストマーカーの定義
pytest_plugins = []

def pytest_configure(config):
    """pytestの設定"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require DB)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (no external dependencies)"
    )
