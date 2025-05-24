from fastapi import Request, Response
import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address

# 構造化ロガー
logger = structlog.get_logger(__name__)

# クライアントIPアドレスに基づくリミッター
# Redis統合が必要な場合は、slowapi.extension.Redis をインポートし、storage_uri を設定
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # デフォルトの制限
)

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