import logging
import sys
import os
import json
import ipaddress
import structlog
import contextvars
from collections.abc import Mapping
from typing import Dict, Any, Optional, List

from libkoiki.core.config import settings

# グローバル変数
_logging_configured = False
REDACTED = "[REDACTED]"
REDACTED_CYCLE = "[REDACTED:CYCLE]"
REDACTED_DEPTH_LIMIT = "[REDACTED:DEPTH_LIMIT]"
MAX_SANITIZE_DEPTH = 5
LOG_CATEGORY_NORMAL = "normal"
LOG_CATEGORY_SECURITY = "security"
LOG_CATEGORY_AUDIT = "audit"
INTERNAL_LOG_CATEGORY_KEY = "_log_category"

SENSITIVE_EXACT_KEYS = {
    "password",
    "current_password",
    "new_password",
    "hashed_password",
    "token",
    "token_prefix",
    "access_token",
    "refresh_token",
    "reset_token",
    "id_token",
    "relay_state",
    "relay_nonce",
    "oauth_state",
    "sso_state",
    "login_ticket",
    "ticket_id",
    "authorization",
    "cookie",
    "session_id",
    "session_token",
    "session_key",
    "secret",
    "client_secret",
    "jwt_secret",
    "private_key",
    "signing_key",
    "saml_response",
    "assertion",
}

# リクエストコンテキスト用の contextvars
request_context = contextvars.ContextVar("request_context", default={})


def _normalize_key_part(key: str) -> str:
    """ログキー判定用にキーを正規化"""
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _candidate_keys(key: Any) -> set[str]:
    """元キーと末尾キーの両方を判定候補にする"""
    if not isinstance(key, str):
        return set()

    normalized = _normalize_key_part(key)
    candidates = {normalized}

    if "." in normalized:
        candidates.add(normalized.split(".")[-1])

    return candidates


def _is_privileged_log(logger_name: Optional[str]) -> bool:
    """security / audit ログかどうかを判定"""
    return logger_name in {"security", "audit"}


def _get_logger_name(logger: Any) -> Optional[str]:
    """processor から logger 名を安全に取得する"""
    try:
        return getattr(logger, "name", None)
    except Exception:
        return None


def _normalize_log_category(value: Any) -> Optional[str]:
    """ログカテゴリ文字列を正規化する"""
    if not isinstance(value, str):
        return None

    normalized = _normalize_key_part(value)
    if normalized in {
        LOG_CATEGORY_NORMAL,
        LOG_CATEGORY_SECURITY,
        LOG_CATEGORY_AUDIT,
    }:
        return normalized

    return None


def resolve_log_category(
    logger_name: Optional[str] = None,
    event_dict: Optional[Mapping[str, Any]] = None,
) -> str:
    """logger 名または event dict からログカテゴリを解決する"""
    if isinstance(event_dict, Mapping):
        category_from_event = _normalize_log_category(event_dict.get(INTERNAL_LOG_CATEGORY_KEY))
        if category_from_event:
            return category_from_event

        if event_dict.get("audit") is True:
            return LOG_CATEGORY_AUDIT

    category_from_logger = _normalize_log_category(logger_name)
    if category_from_logger:
        return category_from_logger

    return LOG_CATEGORY_NORMAL


def _is_privileged_log_category(log_category: str) -> bool:
    """security / audit カテゴリかどうかを判定"""
    return log_category in {LOG_CATEGORY_SECURITY, LOG_CATEGORY_AUDIT}


def mask_email(value: Any) -> Any:
    """email を通常ログ向けに部分マスクする"""
    if not isinstance(value, str) or "@" not in value:
        return value

    local_part, domain = value.split("@", 1)
    if not local_part:
        return REDACTED

    if len(local_part) == 1:
        masked_local = "*"
    elif len(local_part) == 2:
        masked_local = f"{local_part[0]}*"
    else:
        masked_local = f"{local_part[0]}***"

    return f"{masked_local}@{domain}"


def mask_ip_address(value: Any) -> Any:
    """IP アドレスを通常ログ向けに部分マスクする"""
    if not isinstance(value, str):
        return value

    try:
        ip_obj = ipaddress.ip_address(value)
    except ValueError:
        return value

    if ip_obj.version == 4:
        octets = value.split(".")
        return f"{octets[0]}.{octets[1]}.{octets[2]}.xxx"

    exploded = ip_obj.exploded.split(":")
    return ":".join(exploded[:4] + ["xxxx", "xxxx", "xxxx", "xxxx"])


def mask_user_agent(value: Any) -> Any:
    """user agent を通常ログ向けに簡易化する"""
    if not isinstance(value, str):
        return value

    collapsed = " ".join(value.split())
    if not collapsed:
        return collapsed

    return collapsed.split(" ", 1)[0]


def is_sensitive_key(key: Any) -> bool:
    """機密キーかどうかを判定"""
    candidates = _candidate_keys(key)
    return bool(candidates & SENSITIVE_EXACT_KEYS)


def get_error_type_name(exc: Any) -> str:
    """例外オブジェクトからログ向けの型名を返す"""
    return type(exc).__name__


def get_log_field_names(
    payload: Any,
    *,
    allowed_fields: Optional[list[str]] = None,
) -> list[str]:
    """ログに残してよい入力フィールド名だけを返す"""
    if payload is None:
        return []

    mapping: Optional[Mapping[Any, Any]] = None

    if isinstance(payload, Mapping):
        mapping = payload
    elif hasattr(payload, "model_dump"):
        try:
            mapping = payload.model_dump(exclude_unset=True)
        except TypeError:
            mapping = payload.model_dump()
    elif hasattr(payload, "dict"):
        try:
            mapping = payload.dict(exclude_unset=True)
        except TypeError:
            mapping = payload.dict()
    elif hasattr(payload, "__dict__"):
        payload_dict = getattr(payload, "__dict__", None)
        if isinstance(payload_dict, Mapping):
            mapping = payload_dict

    if mapping is None:
        return []

    allowed = {_normalize_key_part(field) for field in allowed_fields or []}
    field_names: list[str] = []
    for key in mapping.keys():
        if not isinstance(key, str):
            continue
        if key.startswith("_"):
            continue
        normalized = _normalize_key_part(key)
        if not normalized:
            continue
        if is_sensitive_key(key):
            continue
        if allowed and normalized not in allowed:
            continue
        field_names.append(key)

    return sorted(set(field_names))


def sanitize_log_value(
    key: Any,
    value: Any,
    logger_name: Optional[str] = None,
    event_dict: Optional[Dict[str, Any]] = None,
    log_category: Optional[str] = None,
    _seen: Optional[set[int]] = None,
    _depth: int = 0,
) -> Any:
    """単一のログ値を安全化する"""

    if _depth > MAX_SANITIZE_DEPTH:
        return REDACTED_DEPTH_LIMIT

    if is_sensitive_key(key):
        return REDACTED

    resolved_category = log_category or resolve_log_category(
        logger_name=logger_name,
        event_dict=event_dict,
    )

    candidates = _candidate_keys(key)
    if not _is_privileged_log_category(resolved_category):
        if "email" in candidates:
            return mask_email(value)
        if "ip_address" in candidates:
            return mask_ip_address(value)
        if "user_agent" in candidates:
            return mask_user_agent(value)

    if isinstance(value, Mapping):
        return sanitize_mapping(
            value,
            logger_name=logger_name,
            event_dict=event_dict,
            log_category=resolved_category,
            _seen=_seen,
            _depth=_depth + 1,
        )

    if isinstance(value, list):
        return [
            sanitize_log_value(
                None,
                item,
                logger_name=logger_name,
                event_dict=event_dict,
                log_category=resolved_category,
                _seen=_seen,
                _depth=_depth + 1,
            )
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            sanitize_log_value(
                None,
                item,
                logger_name=logger_name,
                event_dict=event_dict,
                log_category=resolved_category,
                _seen=_seen,
                _depth=_depth + 1,
            )
            for item in value
        )

    if isinstance(value, set):
        return {
            sanitize_log_value(
                None,
                item,
                logger_name=logger_name,
                event_dict=event_dict,
                log_category=resolved_category,
                _seen=_seen,
                _depth=_depth + 1,
            )
            for item in value
        }

    return value


def sanitize_mapping(
    mapping: Mapping[str, Any],
    logger_name: Optional[str] = None,
    event_dict: Optional[Dict[str, Any]] = None,
    log_category: Optional[str] = None,
    _seen: Optional[set[int]] = None,
    _depth: int = 0,
) -> Dict[str, Any]:
    """mapping を再帰的に安全化する"""

    if _depth > MAX_SANITIZE_DEPTH:
        return {"_sanitized": REDACTED_DEPTH_LIMIT}

    seen = _seen if _seen is not None else set()
    mapping_id = id(mapping)
    if mapping_id in seen:
        return {"_sanitized": REDACTED_CYCLE}

    seen.add(mapping_id)
    try:
        root_event_dict = event_dict or mapping
        resolved_category = log_category or resolve_log_category(
            logger_name=logger_name,
            event_dict=root_event_dict,
        )
        sanitized: Dict[str, Any] = {}
        for current_key, current_value in mapping.items():
            if current_key == INTERNAL_LOG_CATEGORY_KEY:
                continue
            sanitized[current_key] = sanitize_log_value(
                current_key,
                current_value,
                logger_name=logger_name,
                event_dict=root_event_dict,
                log_category=resolved_category,
                _seen=seen,
                _depth=_depth,
            )
        return sanitized
    finally:
        seen.discard(mapping_id)


def sanitize_event_dict(logger, method_name, event_dict):
    """structlog event dict 全体を安全化する processor"""
    del method_name  # 未使用

    if not isinstance(event_dict, dict):
        return event_dict

    try:
        logger_name = _get_logger_name(logger)
        sanitized = sanitize_mapping(
            event_dict,
            logger_name=logger_name,
            event_dict=event_dict,
        )
        log_category = resolve_log_category(
            logger_name=logger_name,
            event_dict=event_dict,
        )
        request_http = sanitized.get("request.http")
        if isinstance(request_http, Mapping) and log_category == LOG_CATEGORY_NORMAL:
            sanitized["request.http"] = {
                key: request_http[key]
                for key in ("method", "path", "request_id")
                if key in request_http
            }
        return sanitized
    except Exception:
        return event_dict

# リクエストコンテキスト管理ヘルパー関数
def bind_request_context(**kwargs):
    """リクエストコンテキストに情報をバインド"""
    try:
        context = request_context.get().copy()
        context.update(kwargs)
        request_context.set(context)
    except Exception as e:
        # エラーが起きても処理を続行
        print(f"Error in bind_request_context: {e}")

def clear_request_context():
    """リクエストコンテキストをクリア"""
    try:
        request_context.set({})
    except Exception as e:
        print(f"Error in clear_request_context: {e}")


def get_request_context() -> Dict[str, Any]:
    """現在のリクエストコンテキストを安全に取得する"""
    try:
        context = request_context.get()
        if isinstance(context, dict):
            return context.copy()
    except Exception:
        pass
    return {}

# リクエスト情報をログに追加するプロセッサ
def add_request_info(logger, method_name, event_dict):
    """リクエスト情報をログに追加する安全なプロセッサ"""
    if not isinstance(event_dict, dict):
        return event_dict
    try:
        ctx = request_context.get()
        if ctx:
            # 辞書の浅いコピーをマージ（深いコピーではない）
            for k, v in ctx.items():
                event_dict[f"request.{k}"] = v
    except Exception:
        pass
    return event_dict

# カスタムプロセッサ（すべて防御的コーディング）
def add_timestamp(logger, method_name, event_dict):
    """タイムスタンプを追加する安全なプロセッサ"""
    import datetime
    from zoneinfo import ZoneInfo
    if not isinstance(event_dict, dict):
        return event_dict
    try:
        tz = datetime.timezone.utc
        if settings.LOG_TIMEZONE != "UTC":
            try:
                tz = ZoneInfo(settings.LOG_TIMEZONE)
            except Exception:
                pass  # Fallback to UTC on error
        
        event_dict["timestamp"] = datetime.datetime.now(tz).isoformat()
    except (TypeError, AttributeError):
        pass
    return event_dict

def add_app_info(logger, method_name, event_dict):
    """アプリケーション情報を追加する安全なプロセッサ"""
    if not isinstance(event_dict, dict):
        return event_dict
    try:
        event_dict["app"] = settings.APP_NAME
        event_dict["env"] = settings.APP_ENV
    except (TypeError, AttributeError):
        pass
    return event_dict

def rename_event_key(logger, method_name, event_dict):
    """'event'キーを'message'に変更する安全なプロセッサ"""
    if not isinstance(event_dict, dict):
        return event_dict
    try:
        if "event" in event_dict:
            event_dict["message"] = event_dict.pop("event")
    except (TypeError, AttributeError):
        pass
    return event_dict

# シンプルなJSONレンダラー
class SafeJsonRenderer:
    def __call__(self, logger, name, event_dict):
        """安全にJSONに変換するレンダラー"""
        if not isinstance(event_dict, dict):
            return "{}"
        
        try:
            return json.dumps(event_dict, default=str)
        except Exception:
            return "{}"

# シンプルなコンソールレンダラー
class SafeConsoleRenderer:
    def __call__(self, logger, name, event_dict):
        """安全にコンソール表示用に変換するレンダラー"""
        if not isinstance(event_dict, dict):
            return "Log event"
        
        try:
            if "message" in event_dict:
                msg = event_dict.pop("message")
                if event_dict:
                    return f"{msg} {event_dict}"
                return msg
            return str(event_dict)
        except Exception:
            return "Log event"

# ログ設定
def setup_logging():
    """最小限のstructlog設定"""
    global _logging_configured
    if _logging_configured:
        return

    # 基本的なログレベル設定
    log_level_str = settings.LOG_LEVEL.upper() if hasattr(settings, "LOG_LEVEL") else "INFO"
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # 標準のPythonロギングを設定
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout,
    )

    # 開発環境かどうか
    is_dev = getattr(settings, "APP_ENV", "development") == "development" or getattr(settings, "DEBUG", False)
    
    # structlog設定
    try:
        # 最小限のプロセッサチェーン
        processors = [
            add_timestamp,  # 安全なタイムスタンププロセッサ
            add_app_info,   # 安全なアプリ情報プロセッサ
            add_request_info,  # リクエスト情報追加プロセッサを追加
            rename_event_key,  # 安全なキー名変換プロセッサ
            sanitize_event_dict,  # renderer 直前で event dict を安全化
            SafeConsoleRenderer() if is_dev else SafeJsonRenderer()  # 安全なレンダラー
        ]
        
        # structlog設定
        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        print(f"Logging configured with level: {log_level_str}")
    except Exception as e:
        print(f"Failed to configure structured logging: {e}")
        # 最低限のログ機能は確保

    _logging_configured = True

# シンプルな監査ログ設定
def setup_audit_logging():
    """シンプル化した監査ログ設定"""
    try:
        audit_log_file = os.getenv("AUDIT_LOG_FILE", "audit.log")
        audit_logger = logging.getLogger("audit")
        
        # 既存のハンドラがあれば削除
        for h in audit_logger.handlers[:]:
            audit_logger.removeHandler(h)
            
        # ファイルハンドラ追加
        handler = logging.FileHandler(audit_log_file)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        audit_logger.addHandler(handler)
        
        print("Audit logging configured")
    except Exception as e:
        print(f"Failed to configure audit logging: {e}")

# 構造化ロガー取得関数
def get_logger(name=None):
    """構造化ロガーを取得する"""
    if not _logging_configured:
        setup_logging()
    return structlog.get_logger(name)
