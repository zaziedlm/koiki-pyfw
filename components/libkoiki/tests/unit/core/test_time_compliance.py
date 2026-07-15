
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

    def test_role_model_created_at_uses_database_server_default(self):
        """RoleModelの作成時刻はDBのnow()で設定する。"""
        column = RoleModel.created_at.expression

        assert column.default is None
        assert column.server_default is not None

    def test_permission_model_created_at_uses_database_server_default(self):
        """PermissionModelの作成時刻はDBのnow()で設定する。"""
        column = PermissionModel.created_at.expression

        assert column.default is None
        assert column.server_default is not None
