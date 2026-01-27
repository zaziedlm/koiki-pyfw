
import pytest
from datetime import datetime, timezone

from libkoiki.core import logging
from libkoiki.core import logging as logging_module
from libkoiki.models.role import RoleModel
from libkoiki.models.permission import PermissionModel


class TestTimeCompliance:
    """日付時刻のコンプライアンステスト"""

    def test_logging_timestamp_utc_default(self, monkeypatch):
        """ログのタイムスタンプがデフォルトでUTCであることを確認"""
        monkeypatch.setattr(logging_module.settings, "LOG_TIMEZONE", "UTC")
        
        event_dict = {}
        logging.add_timestamp(None, None, event_dict)
        
        timestamp_str = event_dict.get("timestamp")
        assert timestamp_str is not None
        assert "+00:00" in timestamp_str

    def test_logging_timestamp_jst_config(self, monkeypatch):
        """ログのタイムスタンプがJSTに設定できることを確認"""
        monkeypatch.setattr(logging_module.settings, "LOG_TIMEZONE", "Asia/Tokyo")
        
        event_dict = {}
        logging.add_timestamp(None, None, event_dict)
        
        timestamp_str = event_dict.get("timestamp")
        assert timestamp_str is not None
        assert "+09:00" in timestamp_str

    def test_role_model_defaults(self):
        """RoleModelの日付デフォルトがtimezone-awareであることを確認"""
        col_default = RoleModel.created_at.expression.default
        
        # デフォルトがcallableであることを確認
        assert col_default is not None, "created_at should have a default value"
        assert col_default.is_callable, "created_at default should be callable"
        
        # デフォルト値を実行してtimezone-awareであることを確認
        val = col_default.arg(None)
        assert isinstance(val, datetime), "Default value should be datetime"
        assert val.tzinfo is not None, "Datetime should be timezone-aware"
        assert val.tzinfo == timezone.utc, "Timezone should be UTC"

    def test_permission_model_defaults(self):
        """PermissionModelの日付デフォルトがtimezone-awareであることを確認"""
        col_default = PermissionModel.created_at.expression.default
        
        # デフォルトがcallableであることを確認
        assert col_default is not None, "created_at should have a default value"
        assert col_default.is_callable, "created_at default should be callable"
        
        # デフォルト値を実行してtimezone-awareであることを確認
        val = col_default.arg(None)
        assert isinstance(val, datetime), "Default value should be datetime"
        assert val.tzinfo is not None, "Datetime should be timezone-aware"
        assert val.tzinfo == timezone.utc, "Timezone should be UTC"
