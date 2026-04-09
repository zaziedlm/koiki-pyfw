# src/core/error_handlers.py
import logging
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from libkoiki.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BaseAppException,
    ResourceNotFoundException,
    ValidationException,
)

logger = structlog.get_logger(__name__)


def _get_client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _safe_http_headers(headers: Any) -> bool:
    return bool(headers)


def _summarize_db_exception(exc: SQLAlchemyError) -> dict[str, Any]:
    summary = {
        "db_exception_type": type(exc).__name__,
    }

    original_exc = getattr(exc, "orig", None)
    if original_exc is not None:
        summary["db_driver_error_type"] = type(original_exc).__name__

    return summary


def _sanitize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for error in errors:
        cleaned: dict[str, Any] = {
            "type": error.get("type"),
            "msg": error.get("msg"),
        }

        loc = error.get("loc")
        if isinstance(loc, (list, tuple)):
            cleaned["loc"] = [str(item) for item in loc]
        elif loc is not None:
            cleaned["loc"] = [str(loc)]

        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            safe_ctx = {}
            for ctx_key, ctx_val in ctx.items():
                if ctx_key == "input":
                    continue
                if isinstance(ctx_val, Exception):
                    safe_ctx[ctx_key] = type(ctx_val).__name__
                elif isinstance(ctx_val, (str, int, float, bool)) or ctx_val is None:
                    safe_ctx[ctx_key] = ctx_val
                else:
                    safe_ctx[ctx_key] = type(ctx_val).__name__
            if safe_ctx:
                cleaned["ctx"] = safe_ctx

        sanitized.append(cleaned)
    return sanitized


async def http_exception_handler(request: Request, exc: HTTPException):
    """FastAPI の HTTPException を処理し、ログとJSONレスポンスを生成"""
    logger.warning(
        "HTTP Exception caught",
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
        client=_get_client_host(request),
        has_headers=_safe_http_headers(exc.headers),
        error_type=type(exc).__name__,
        response_detail_type=type(exc.detail).__name__,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


async def base_app_exception_handler(request: Request, exc: BaseAppException):
    """カスタムアプリケーション例外 (BaseAppException) のハンドラー"""
    error_code = getattr(exc, "error_code", "APPLICATION_ERROR")
    log_level = "warning"  # デフォルトは警告レベル
    log_exc_info = False  # デフォルトではスタックトレースは不要

    # 例外タイプに応じてログレベルや詳細度を調整
    if isinstance(exc, ResourceNotFoundException):
        log_level = "info"
        log_message = "Resource not found"
    elif isinstance(exc, ValidationException):
        log_level = "warning"
        log_message = "Validation failed"
    elif isinstance(exc, AuthorizationException):
        log_level = "warning"
        log_message = "Authorization failed"
    elif isinstance(exc, AuthenticationException):
        log_level = "warning"  # 認証失敗は警告レベル
        log_message = "Authentication failed"
    else:  # その他の BaseAppException
        log_level = "error"
        log_message = "Unhandled application exception"
        log_exc_info = True  # スタックトレースを出力

    # structlog を使用してログ記録
    logger.log(
        getattr(
            logging, log_level.upper(), logging.WARNING
        ),  # 文字列からログレベル定数を取得
        log_message,
        status_code=exc.status_code,
        error_code=error_code,
        path=request.url.path,
        method=request.method,
        client=_get_client_host(request),
        error_type=type(exc).__name__,
        exc_info=log_exc_info,  # 必要に応じてスタックトレースを追加
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": error_code},
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPIのリクエストバリデーションエラー (422) ハンドラー"""
    errors = _sanitize_validation_errors(exc.errors())
    logger.warning(
        "Request validation error",
        errors=errors,
        path=request.url.path,
        method=request.method,
        client=_get_client_host(request),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "error_code": "VALIDATION_ERROR"},
    )


async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    """データベース関連エラー (SQLAlchemyError) の汎用ハンドラー"""
    error_code = "DB_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An unexpected database error occurred."
    log_level = "error"
    log_exc_info = True

    if isinstance(exc, IntegrityError):  # 一意制約違反など
        status_code = status.HTTP_409_CONFLICT
        detail = "Database integrity error. Resource might already exist or constraint violated."
        error_code = "DB_INTEGRITY_ERROR"
        log_level = "warning"
        log_exc_info = False  # 通常スタックトレースは不要
    elif isinstance(exc, NoResultFound):  # SQLAlchemy 2.0 の .one() などで発生
        status_code = status.HTTP_404_NOT_FOUND
        detail = "The requested database record was not found."
        error_code = "DB_NOT_FOUND"
        log_level = "info"
        log_exc_info = False
    # 他にも特定のDBエラー (e.g., DeadlockError) をハンドリング可能

    logger.log(
        getattr(logging, log_level.upper(), logging.ERROR),
        f"Database exception: {type(exc).__name__}",
        status_code=status_code,
        error_code=error_code,
        path=request.url.path,
        method=request.method,
        client=_get_client_host(request),
        error_type=type(exc).__name__,
        **_summarize_db_exception(exc),
        exc_info=log_exc_info,  # エラー時はスタックトレースを出力
    )

    # ユーザーには汎用的なメッセージを返す
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_code": error_code},
    )


# RateLimitExceeded ハンドラは main.py で slowapi のデフォルトを使用するため、ここでは不要
# async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded): ...


async def generic_exception_handler(request: Request, exc: Exception):
    """その他の予期せぬエラー (Exception) のハンドラー"""
    logger.error(
        "Unhandled internal server error",
        path=request.url.path,
        method=request.method,
        client=_get_client_host(request),
        error_type=type(exc).__name__,
        exc_info=True,  # 必ずスタックトレースを出力
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred.",
            "error_code": "INTERNAL_ERROR",
        },
    )


def setup_exception_handlers(app: FastAPI):
    """アプリケーションに例外ハンドラーを登録する"""
    app.add_exception_handler(
        HTTPException, http_exception_handler
    )  # FastAPI自身のHTTPExceptionも捕捉
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, db_exception_handler)
    # RateLimitExceeded ハンドラは main.py で slowapi デフォルトを使用
    # app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_exception_handler(
        Exception, generic_exception_handler
    )  # 最も汎用的なハンドラを最後に登録
    logger.info("Global exception handlers configured.")
