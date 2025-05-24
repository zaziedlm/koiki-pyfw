# src/core/middleware.py
import time
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import StreamingResponse
from starlette.types import ASGIApp
import structlog
import uuid # リクエストID用
from datetime import datetime, timezone # timezone をインポート

# from libkoiki.core.security import get_user_from_token # パフォーマンス影響大のため注意
# from libkoiki.db.session import get_db # ミドルウェアでのDBアクセスは避けるべき

from libkoiki.core.logging import bind_request_context, clear_request_context # コンテキスト管理ヘルパー

# 監査ログ専用のロガーを取得 (logging.pyで設定されている想定)
audit_logger = structlog.get_logger("audit")
access_logger = structlog.get_logger("api.access") # アクセスログ用 (Uvicornログを処理する場合、これは不要かも)

class RequestContextLogMiddleware(BaseHTTPMiddleware):
    """
    リクエストIDを生成し、基本的なリクエスト情報を structlog のコンテキストにバインドするミドルウェア。
    これが AuditLogMiddleware や AccessLogMiddleware より先に実行される必要がある。
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # リクエストID生成 (ヘッダーにあればそれを使う)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # リクエスト情報をコンテキストにバインド
        http_context = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "client": request.client.host if request.client else "unknown",
            "request_id": request_id,
            "user_agent": request.headers.get("User-Agent", ""),
        }
        # ユーザー情報は認証後に別の場所でバインドする方が良いかもしれない
        # user_context = {"id": None, "email": None} # 初期値
        bind_request_context(http=http_context) # user=user_context

        # レスポンスにリクエストIDヘッダーを追加
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # リクエスト処理後にコンテキストをクリア
        clear_request_context()
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    監査ログを記録するミドルウェア。
    RequestContextLogMiddleware の後に実行される想定。
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        user_id: Optional[int] = None
        user_email: Optional[str] = None # 取得できれば

        # --- リクエスト処理 ---
        response = await call_next(request) # 先にレスポンスを取得
        process_time = time.time() - start_time
        status_code = response.status_code

        # --- ユーザー情報の取得 (より軽量な方法を検討) ---
        # `request.state` に認証ミドルウェアがユーザー情報を格納している場合
        if hasattr(request.state, "current_user") and request.state.current_user:
             user = request.state.current_user
             if hasattr(user, 'id'): user_id = user.id
             if hasattr(user, 'email'): user_email = user.email
        # または、トークンデコードのみ行う（DBアクセスなし）
        # elif "Authorization" in request.headers and request.headers["Authorization"].startswith("Bearer "):
        #     token = request.headers["Authorization"].split(" ")[1]
        #     try:
        #         from jose import jwt
        #         from libkoiki.core.config import settings
        #         from libkoiki.schemas.token import TokenPayload
        #         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}) # 有効期限切れでもIDは取得試行
        #         token_data = TokenPayload(**payload)
        #         user_id = int(token_data.sub) if token_data.sub else None
        #     except Exception:
        #         pass # トークン無効など

        # --- structlog コンテキストからリクエスト情報を取得 ---
        log_context = structlog.contextvars.get_contextvars()
        http_context = log_context.get("http", {})
        request_id = http_context.get("request_id", "unknown")
        client_ip = http_context.get("client", "unknown")
        method = http_context.get("method", request.method) # コンテキストになければリクエストから
        path = http_context.get("path", request.url.path)
        query_params = http_context.get("query")

        # --- 監査ログ記録 ---
        log_entry = {
            "audit": True, # 監査ログフラグ
            "timestamp": datetime.now(timezone.utc).isoformat(), # ISO形式タイムスタンプ
            "user.id": user_id,
            "user.email": user_email,
            "http.client_ip": client_ip,
            "http.method": method,
            "http.path": path,
            "http.query": query_params,
            "http.request_id": request_id,
            "http.status_code": status_code,
            "event.action": f"{method}_{path.replace('/', '_').strip('_')}", # アクション名
            "event.outcome": "success" if 200 <= status_code < 400 else "failure",
            "event.duration_ms": int(process_time * 1000),
            # "resource.type": "?", # 操作対象リソースの種類 (例: 'user', 'todo')
            # "resource.id": "?",   # 操作対象リソースのID (パスパラメータなどから取得)
            # "request.body": request_body, # 必要なら記録 (機密情報に注意)
        }

        # 監査ロガーを使用してログを出力 (structlogがJSON化してくれる)
        audit_logger.info("API Request Processed", **log_entry)

        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティ関連のHTTPヘッダーを追加するミドルウェア"""
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        # HSTS: HTTPS接続を強制 (max-ageは秒単位、例: 1年)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Content-Type スニッフィング防止
        response.headers["X-Content-Type-Options"] = "nosniff"
        # クリックジャッキング防止
        response.headers["X-Frame-Options"] = "DENY" # または "SAMEORIGIN"
        # リファラポリシー
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content Security Policy (CSP) - アプリケーション固有の設定が必要
        # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none';"
        # Permissions Policy (旧 Feature Policy) - アプリケーション固有の設定が必要
        # response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response


# オプション: Uvicornのアクセスログを無効にして、このミドルウェアで代用する場合
class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    基本的なアクセスログを structlog を使って記録するミドルウェア。
    RequestContextLogMiddleware の後に実行される想定。
    Uvicorn のアクセスログを structlog で処理する場合は不要。
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        # リクエスト処理
        response = await call_next(request)

        process_time = time.time() - start_time
        status_code = response.status_code

        # structlog コンテキストから情報を取得
        log_context = structlog.contextvars.get_contextvars()
        http_context = log_context.get("http", {})
        user_context = log_context.get("user", {}) # ユーザー情報があれば

        # アクセスログとして出力
        access_logger.info(
            "Access log",
            # コンテキストからの情報を展開
            **http_context,
            **user_context,
             # レスポンス情報
            http={"status_code": status_code}, # ネストさせる場合
            # status_code=status_code, # フラットにする場合
            event={"duration_ms": int(process_time * 1000)},
        )

        return response

# --- ミドルウェアの適用順序 (main.py で指定) ---
# 1. CORSMiddleware (必要なら最初の方)
# 2. RequestContextLogMiddleware (リクエストIDと基本情報をコンテキストに)
# 3. AuditLogMiddleware (コンテキスト情報を使って監査ログ記録)
# 4. SecurityHeadersMiddleware (レスポンスヘッダ追加)
# 5. AccessLogMiddleware (オプション: コンテキスト情報を使ってアクセスログ記録)
# ... その他のミドルウェア ...
# (レートリミットミドルウェアは通常 AuditLog の前後)
