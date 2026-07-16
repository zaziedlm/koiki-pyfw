from typing import Any

import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address

from libkoiki.core.config import settings

# 構造化ロガー
logger = structlog.get_logger(__name__)

# クライアントIPアドレスに基づくリミッター
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    strategy=settings.RATE_LIMIT_STRATEGY,
)


def configure_limiter(
    *,
    enabled: bool,
    default_limit: str,
    strategy: str,
    storage_uri: str | None = None,
    storage_options: dict[str, Any] | None = None,
) -> Limiter:
    """Configure the shared limiter used by endpoint decorators.

    slowapi decorators close over the Limiter instance at import time, so the
    application must reconfigure this shared object instead of replacing it.
    """

    route_limits = limiter._route_limits
    dynamic_route_limits = limiter._dynamic_route_limits
    marked_for_limiting = limiter._Limiter__marked_for_limiting
    exempt_routes = limiter._exempt_routes
    request_filters = limiter._request_filters

    Limiter.__init__(
        limiter,
        key_func=get_remote_address,
        enabled=enabled,
        default_limits=[default_limit] if enabled else [],
        strategy=strategy,
        storage_uri=storage_uri,
        storage_options=storage_options or {},
    )

    limiter._route_limits = route_limits
    limiter._dynamic_route_limits = dynamic_route_limits
    limiter._Limiter__marked_for_limiting = marked_for_limiting
    limiter._exempt_routes = exempt_routes
    limiter._request_filters = request_filters
    return limiter

# 以下のデコレータ部分を削除または修正
# @limiter.request_filter
# def log_limiter_info(request: Request) -> bool:
#     """
#     レート制限のログを記録し、特定のリクエストを除外するためのフィルタ
#     """
#     # 例: 特定のパスを除外
#     if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
#         return True  # Trueを返すとこのリクエストはレート制限から除外される
#     
#     # ロギング
#     client_ip = get_remote_address(request)
#     path = request.url.path
#     logger.debug("API request", client_ip=client_ip, path=path)
#     
#     # デフォルトでは除外しない
#     return False
