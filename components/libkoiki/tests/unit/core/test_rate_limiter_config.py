from fastapi import Request

from libkoiki.core.rate_limiter import configure_limiter, limiter


async def _limited_endpoint(request: Request):
    return {"ok": True}


def test_configure_limiter_preserves_decorated_route_limits():
    route_key = f"{_limited_endpoint.__module__}.{_limited_endpoint.__name__}"
    previous_limits = dict(limiter._route_limits)
    previous_dynamic_limits = dict(limiter._dynamic_route_limits)
    previous_marked = dict(limiter._Limiter__marked_for_limiting)
    previous_enabled = limiter.enabled
    previous_default_limits = list(limiter._default_limits)
    previous_strategy = limiter._strategy
    previous_storage_uri = limiter._storage_uri
    previous_storage_options = dict(limiter._storage_options)
    previous_storage = limiter._storage
    previous_limiter_backend = limiter._limiter
    previous_fallback_limiter = limiter._fallback_limiter
    previous_storage_dead = limiter._storage_dead

    try:
        limiter.limit("2/minute")(_limited_endpoint)
        assert route_key in limiter._route_limits

        configured = configure_limiter(
            enabled=True,
            default_limit="9/minute",
            strategy="fixed-window",
            storage_uri="memory://",
            storage_options={"test_option": "value"},
        )

        assert configured is limiter
        assert limiter.enabled is True
        assert limiter._storage_uri == "memory://"
        assert limiter._storage_options["test_option"] == "value"
        assert route_key in limiter._route_limits
        assert str(limiter._route_limits[route_key][0].limit) == "2 per 1 minute"
    finally:
        limiter._route_limits = previous_limits
        limiter._dynamic_route_limits = previous_dynamic_limits
        limiter._Limiter__marked_for_limiting = previous_marked
        limiter.enabled = previous_enabled
        limiter._default_limits = previous_default_limits
        limiter._strategy = previous_strategy
        limiter._storage_uri = previous_storage_uri
        limiter._storage_options = previous_storage_options
        limiter._storage = previous_storage
        limiter._limiter = previous_limiter_backend
        limiter._fallback_limiter = previous_fallback_limiter
        limiter._storage_dead = previous_storage_dead
