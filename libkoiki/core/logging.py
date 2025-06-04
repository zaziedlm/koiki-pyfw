import logging
import sys
import os
import json
import structlog
import contextvars
from typing import Dict, Any, Optional, List

from libkoiki.core.config import settings

# グローバル変数
_logging_configured = False

# リクエストコンテキスト用の contextvars
request_context = contextvars.ContextVar("request_context", default={})

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
    if not isinstance(event_dict, dict):
        return event_dict
    try:
        event_dict["timestamp"] = datetime.datetime.now().isoformat()
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