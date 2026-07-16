from unittest.mock import AsyncMock

import pytest

from libkoiki.core.rate_limiter import limiter
from koiki_ref_app import app_factory


@pytest.mark.asyncio
async def test_lifespan_configures_shared_decorator_limiter(monkeypatch):
    previous_enabled = limiter.enabled
    previous_default_limits = list(limiter._default_limits)
    previous_strategy = limiter._strategy
    previous_storage_uri = limiter._storage_uri
    previous_storage_options = dict(limiter._storage_options)
    previous_storage = limiter._storage
    previous_limiter_backend = limiter._limiter
    previous_fallback_limiter = limiter._fallback_limiter
    previous_storage_dead = limiter._storage_dead

    monkeypatch.setattr(app_factory, "connect_db", AsyncMock())
    monkeypatch.setattr(app_factory, "disconnect_db", AsyncMock())
    monkeypatch.setattr(app_factory.settings, "REDIS_ENABLED", False)
    monkeypatch.setattr(app_factory.settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(app_factory.settings, "RATE_LIMIT_DEFAULT", "11/minute")
    monkeypatch.setattr(app_factory.settings, "RATE_LIMIT_STRATEGY", "fixed-window")

    app = app_factory.create_app()

    try:
        async with app.router.lifespan_context(app):
            assert app.state.limiter is limiter
            assert limiter.enabled is True
            assert limiter._storage_uri is None
    finally:
        limiter.enabled = previous_enabled
        limiter._default_limits = previous_default_limits
        limiter._strategy = previous_strategy
        limiter._storage_uri = previous_storage_uri
        limiter._storage_options = previous_storage_options
        limiter._storage = previous_storage
        limiter._limiter = previous_limiter_backend
        limiter._fallback_limiter = previous_fallback_limiter
        limiter._storage_dead = previous_storage_dead
