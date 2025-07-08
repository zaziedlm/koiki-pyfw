"""ログインセキュリティサービスユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from libkoiki.services.login_security_service import LoginSecurityService
from libkoiki.models.login_attempt import LoginAttemptModel
from libkoiki.models.user import UserModel


@pytest.mark.unit
class TestLoginSecurityService:
    """ログインセキュリティサービスユニットテスト"""
    
    @pytest.fixture
    def login_security_service(self):
        """ログインセキュリティサービスのインスタンス"""
        # モックリポジトリを作成
        mock_login_attempt_repo = AsyncMock()
        return LoginSecurityService(mock_login_attempt_repo)
    
    @pytest.fixture
    def mock_user(self):
        """モックユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_login_attempt(self):
        """モックログイン試行"""
        attempt = MagicMock(spec=LoginAttemptModel)
        attempt.id = 1
        attempt.email = "test@example.com"
        attempt.user_id = 1
        attempt.ip_address = "127.0.0.1"
        attempt.is_successful = False
        attempt.failure_reason = "invalid_credentials"
        attempt.attempted_at = datetime.now(timezone.utc)
        return attempt
    
    async def test_record_login_attempt_success(
        self,
        login_security_service,
        mock_db_session
    ):
        """ログイン試行記録成功テスト"""
        # ログイン試行リポジトリのモック
        mock_login_attempt_repo = AsyncMock()
        mock_created_attempt = MagicMock(spec=LoginAttemptModel)
        mock_created_attempt.id = 1
        mock_login_attempt_repo.create.return_value = mock_created_attempt
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            result = await login_security_service.record_login_attempt(
                email="test@example.com",
                ip_address="127.0.0.1",
                is_successful=True,
                db=mock_db_session,
                user_id=1,
                user_agent="test_agent",
                failure_reason=None
            )
            
            # 結果検証
            assert result == mock_created_attempt
            mock_login_attempt_repo.create.assert_called_once()
            
            # 作成時の引数を確認
            call_args = mock_login_attempt_repo.create.call_args[0][0]
            assert call_args.email == "test@example.com"
            assert call_args.ip_address == "127.0.0.1"
            assert call_args.is_successful is True
            assert call_args.user_id == 1
    
    async def test_record_login_attempt_failure(
        self,
        login_security_service,
        mock_db_session
    ):
        """ログイン試行記録失敗テスト"""
        # ログイン試行リポジトリのモック
        mock_login_attempt_repo = AsyncMock()
        mock_created_attempt = MagicMock(spec=LoginAttemptModel)
        mock_created_attempt.id = 1
        mock_login_attempt_repo.create.return_value = mock_created_attempt
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            result = await login_security_service.record_login_attempt(
                email="test@example.com",
                ip_address="127.0.0.1",
                is_successful=False,
                db=mock_db_session,
                user_id=None,
                user_agent="test_agent",
                failure_reason="invalid_credentials"
            )
            
            # 結果検証
            assert result == mock_created_attempt
            mock_login_attempt_repo.create.assert_called_once()
            
            # 作成時の引数を確認
            call_args = mock_login_attempt_repo.create.call_args[0][0]
            assert call_args.email == "test@example.com"
            assert call_args.ip_address == "127.0.0.1"
            assert call_args.is_successful is False
            assert call_args.user_id is None
            assert call_args.failure_reason == "invalid_credentials"
    
    async def test_check_login_allowed_success(
        self,
        login_security_service,
        mock_db_session
    ):
        """ログイン許可チェック成功テスト"""
        # ログイン試行リポジトリのモック（失敗試行が少ない）
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.count_failed_attempts_by_email.return_value = 2
        mock_login_attempt_repo.count_failed_attempts_by_ip.return_value = 1
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
                email="test@example.com",
                ip_address="127.0.0.1",
                db=mock_db_session
            )
            
            # 結果検証
            assert is_allowed is True
            assert reason is None
            assert retry_after is None
    
    async def test_check_login_allowed_email_lockout(
        self,
        login_security_service,
        mock_db_session
    ):
        """メールアドレスロックアウトテスト"""
        # ログイン試行リポジトリのモック（メールアドレスの失敗試行が多い）
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.count_failed_attempts_by_email.return_value = 5
        mock_login_attempt_repo.count_failed_attempts_by_ip.return_value = 1
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
                email="test@example.com",
                ip_address="127.0.0.1",
                db=mock_db_session
            )
            
            # 結果検証
            assert is_allowed is False
            assert "Account locked" in reason
            assert retry_after == 900  # 15分
    
    async def test_check_login_allowed_ip_lockout(
        self,
        login_security_service,
        mock_db_session
    ):
        """IPアドレスロックアウトテスト"""
        # ログイン試行リポジトリのモック（IPアドレスの失敗試行が多い）
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.count_failed_attempts_by_email.return_value = 1
        mock_login_attempt_repo.count_failed_attempts_by_ip.return_value = 10
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
                email="test@example.com",
                ip_address="127.0.0.1",
                db=mock_db_session
            )
            
            # 結果検証
            assert is_allowed is False
            assert "IP address blocked" in reason
            assert retry_after == 3600  # 1時間
    
    @patch('asyncio.sleep')
    async def test_apply_progressive_delay_first_attempt(
        self,
        mock_sleep,
        login_security_service,
        mock_db_session
    ):
        """段階的遅延テスト（初回試行）"""
        # ログイン試行リポジトリのモック（失敗試行が少ない）
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.count_failed_attempts_by_email.return_value = 0
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            await login_security_service.apply_progressive_delay(
                email="test@example.com",
                ip_address="127.0.0.1",
                db=mock_db_session
            )
            
            # 結果検証（最小遅延時間）
            mock_sleep.assert_called_once()
            call_args = mock_sleep.call_args[0][0]
            assert call_args >= 0.5  # 最小遅延時間
    
    @patch('asyncio.sleep')
    async def test_apply_progressive_delay_multiple_attempts(
        self,
        mock_sleep,
        login_security_service,
        mock_db_session
    ):
        """段階的遅延テスト（複数試行）"""
        # ログイン試行リポジトリのモック（失敗試行が多い）
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.count_failed_attempts_by_email.return_value = 3
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            await login_security_service.apply_progressive_delay(
                email="test@example.com",
                ip_address="127.0.0.1",
                db=mock_db_session
            )
            
            # 結果検証（遅延時間が増加）
            mock_sleep.assert_called_once()
            call_args = mock_sleep.call_args[0][0]
            assert call_args > 0.5  # 最小遅延時間より大きい
    
    async def test_cleanup_old_attempts_success(
        self,
        login_security_service,
        mock_db_session
    ):
        """古いログイン試行のクリーンアップテスト"""
        # ログイン試行リポジトリのモック
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.delete_old_attempts.return_value = 5
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            deleted_count = await login_security_service.cleanup_old_attempts(
                db=mock_db_session,
                days=30
            )
            
            # 結果検証
            assert deleted_count == 5
            mock_login_attempt_repo.delete_old_attempts.assert_called_once()
            
            # 削除対象の日付を確認
            call_args = mock_login_attempt_repo.delete_old_attempts.call_args[0]
            cutoff_date = call_args[0]
            assert isinstance(cutoff_date, datetime)
            assert cutoff_date < datetime.now(timezone.utc)
    
    async def test_get_login_attempt_stats_success(
        self,
        login_security_service,
        mock_db_session
    ):
        """ログイン試行統計取得テスト"""
        # ログイン試行リポジトリのモック
        mock_login_attempt_repo = AsyncMock()
        mock_login_attempt_repo.count_failed_attempts_by_email.return_value = 3
        mock_login_attempt_repo.count_failed_attempts_by_ip.return_value = 2
        mock_login_attempt_repo.count_successful_attempts_by_email.return_value = 10
        
        with patch.object(login_security_service, 'login_attempt_repository', mock_login_attempt_repo):
            # テスト実行
            stats = await login_security_service.get_login_attempt_stats(
                email="test@example.com",
                ip_address="127.0.0.1",
                db=mock_db_session
            )
            
            # 結果検証
            assert stats["failed_attempts_by_email"] == 3
            assert stats["failed_attempts_by_ip"] == 2
            assert stats["successful_attempts_by_email"] == 10
            assert "lockout_window_start" in stats
            assert isinstance(stats["lockout_window_start"], datetime)