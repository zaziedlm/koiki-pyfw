"""ログインセキュリティサービスユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from libkoiki.services.login_security_service import LoginSecurityService
from libkoiki.models.login_attempt import LoginAttemptModel
from libkoiki.models.user import UserModel


@pytest.mark.unit
class TestLoginSecurityService:
    """ログインセキュリティサービスユニットテスト"""

    @pytest.fixture
    def mock_login_attempt_repo(self):
        repo = AsyncMock()
        repo.set_session = MagicMock()
        return repo

    @pytest.fixture
    def login_security_service(self, mock_login_attempt_repo):
        return LoginSecurityService(mock_login_attempt_repo)

    @pytest.mark.asyncio
    async def test_record_login_attempt_success(
        self,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """ログイン試行記録成功テスト"""
        mock_created_attempt = MagicMock(spec=LoginAttemptModel)
        mock_created_attempt.id = 1
        mock_login_attempt_repo.record_attempt.return_value = mock_created_attempt

        result = await login_security_service.record_login_attempt(
            email="test@example.com",
            ip_address="127.0.0.1",
            is_successful=True,
            db=mock_db_session,
            user_id=1,
            user_agent="test_agent",
            failure_reason=None,
        )

        assert result == mock_created_attempt
        mock_login_attempt_repo.set_session.assert_called_once_with(mock_db_session)
        mock_login_attempt_repo.record_attempt.assert_called_once_with(
            email="test@example.com",
            ip_address="127.0.0.1",
            is_successful=True,
            user_id=1,
            user_agent="test_agent",
            failure_reason=None,
        )

    @pytest.mark.asyncio
    async def test_record_login_attempt_failure(
        self,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """ログイン試行記録失敗テスト"""
        mock_created_attempt = MagicMock(spec=LoginAttemptModel)
        mock_created_attempt.id = 2
        mock_login_attempt_repo.record_attempt.return_value = mock_created_attempt

        result = await login_security_service.record_login_attempt(
            email="test@example.com",
            ip_address="127.0.0.1",
            is_successful=False,
            db=mock_db_session,
            user_id=None,
            user_agent="test_agent",
            failure_reason="invalid_credentials",
        )

        assert result == mock_created_attempt
        mock_login_attempt_repo.record_attempt.assert_called_once_with(
            email="test@example.com",
            ip_address="127.0.0.1",
            is_successful=False,
            user_id=None,
            user_agent="test_agent",
            failure_reason="invalid_credentials",
        )

    @pytest.mark.asyncio
    async def test_check_login_allowed_success(
        self,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """ログイン許可チェック成功テスト（失敗試行が閾値未満）"""
        mock_login_attempt_repo.count_recent_failed_attempts_by_email.return_value = 2
        mock_login_attempt_repo.count_recent_failed_attempts_by_ip.return_value = 1

        is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
            email="test@example.com",
            ip_address="127.0.0.1",
            db=mock_db_session,
        )

        assert is_allowed is True
        assert reason is None
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_check_login_allowed_email_lockout(
        self,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """メールアドレスロックアウトテスト"""
        mock_login_attempt_repo.count_recent_failed_attempts_by_email.return_value = 5
        mock_login_attempt_repo.count_recent_failed_attempts_by_ip.return_value = 1

        is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
            email="test@example.com",
            ip_address="127.0.0.1",
            db=mock_db_session,
        )

        assert is_allowed is False
        assert "Account temporarily locked" in reason
        assert retry_after == 900  # 15分 * 60秒

    @pytest.mark.asyncio
    async def test_check_login_allowed_ip_lockout(
        self,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """IPアドレスロックアウトテスト"""
        mock_login_attempt_repo.count_recent_failed_attempts_by_email.return_value = 1
        mock_login_attempt_repo.count_recent_failed_attempts_by_ip.return_value = 10

        is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
            email="test@example.com",
            ip_address="127.0.0.1",
            db=mock_db_session,
        )

        assert is_allowed is False
        assert "IP temporarily blocked" in reason
        assert retry_after == 900  # lockout_duration_minutes (15) * 60

    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_apply_progressive_delay_no_attempts(
        self,
        mock_sleep,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """段階的遅延テスト（失敗試行なし → sleep呼ばれない）"""
        mock_login_attempt_repo.count_recent_failed_attempts_by_email.return_value = 0
        mock_login_attempt_repo.count_recent_failed_attempts_by_ip.return_value = 0

        await login_security_service.apply_progressive_delay(
            email="test@example.com",
            ip_address="127.0.0.1",
            db=mock_db_session,
        )

        mock_sleep.assert_not_called()

    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_apply_progressive_delay_multiple_attempts(
        self,
        mock_sleep,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """段階的遅延テスト（複数失敗 → sleep呼ばれる）"""
        mock_login_attempt_repo.count_recent_failed_attempts_by_email.return_value = 3
        mock_login_attempt_repo.count_recent_failed_attempts_by_ip.return_value = 0

        await login_security_service.apply_progressive_delay(
            email="test@example.com",
            ip_address="127.0.0.1",
            db=mock_db_session,
        )

        # 3回失敗: delay = min(2^(3-1), 30) = min(4, 30) = 4秒
        mock_sleep.assert_called_once_with(4)

    @pytest.mark.asyncio
    async def test_cleanup_old_attempts_success(
        self,
        login_security_service,
        mock_login_attempt_repo,
        mock_db_session,
    ):
        """古いログイン試行のクリーンアップテスト"""
        mock_login_attempt_repo.cleanup_old_attempts.return_value = 5

        deleted_count = await login_security_service.cleanup_old_attempts(
            db=mock_db_session,
            days=30,
        )

        assert deleted_count == 5
        mock_login_attempt_repo.cleanup_old_attempts.assert_called_once_with(30)
