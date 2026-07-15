import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from koiki_ref_app import app_factory
from koiki_ref_app.core.saml_config import SAMLSettings


def test_terminal_saml_flow_retention_defaults_to_30_days():
    settings = SAMLSettings(_env_file=None)

    assert settings.SAML_TERMINAL_FLOW_RETENTION_DAYS == 30


@pytest.mark.asyncio
async def test_periodic_auth_cleanup_uses_session_factory_initialized_at_startup(
    monkeypatch,
):
    session = object()
    completed = asyncio.Event()
    cleanup = AsyncMock(return_value={"login_attempts": 1})

    @asynccontextmanager
    async def session_factory():
        yield session

    async def record_cleanup(*args, **kwargs):
        completed.set()
        return await cleanup(*args, **kwargs)

    monkeypatch.setattr(app_factory.db_session, "AsyncSessionFactory", session_factory)
    monkeypatch.setattr(app_factory, "cleanup_auth_data", record_cleanup)
    monkeypatch.setattr(app_factory.settings, "AUTH_DATA_CLEANUP_INTERVAL_SECONDS", 0)

    task = asyncio.create_task(app_factory._periodic_auth_data_cleanup())
    try:
        await asyncio.wait_for(completed.wait(), timeout=1)
    finally:
        task.cancel()
        await task

    cleanup.assert_awaited_once_with(
        session,
        login_attempt_retention_days=app_factory.settings.LOGIN_ATTEMPT_RETENTION_DAYS,
        saml_terminal_flow_retention_days=(
            app_factory.saml_settings.SAML_TERMINAL_FLOW_RETENTION_DAYS
        ),
    )
