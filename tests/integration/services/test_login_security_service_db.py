"""ログインセキュリティサービス データベース統合テスト"""
import pytest


@pytest.mark.integration
@pytest.mark.db_integration
class TestLoginSecurityServiceDatabase:
    """ログインセキュリティサービス データベース統合テスト"""
    
    # ====== ログイン試行記録テスト ======
    
    @pytest.mark.asyncio
    async def test_record_login_attempt_success(
        self,
        test_services,
        test_db_session
    ):
        """ログイン試行記録成功テスト（実際のDB使用）"""
        login_security_service = test_services["login_security_service"]
        
        # ログイン試行を記録
        attempt = await login_security_service.record_login_attempt(
            email="security_test@example.com",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            is_successful=True,
            db=test_db_session
        )
        
        # 結果検証
        assert attempt is not None
        assert attempt.email == "security_test@example.com"
        assert attempt.ip_address == "127.0.0.1"
        assert attempt.user_agent == "test-agent"
        assert attempt.is_successful is True
        assert attempt.attempted_at is not None
    
    @pytest.mark.asyncio
    async def test_record_login_attempt_failure(
        self,
        test_services,
        test_db_session
    ):
        """ログイン試行記録失敗テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 失敗したログイン試行を記録
        attempt = await login_security_service.record_login_attempt(
            email="security_fail_test@example.com",
            ip_address="192.168.1.100",
            user_agent="test-agent",
            is_successful=False,
            db=test_db_session
        )
        
        # 結果検証
        assert attempt is not None
        assert attempt.email == "security_fail_test@example.com"
        assert attempt.ip_address == "192.168.1.100"
        assert attempt.is_successful is False

    @pytest.mark.asyncio
    async def test_check_login_allowed_no_limit(
        self,
        test_services,
        test_db_session
    ):
        """ログイン許可チェック（制限なし）テスト"""
        login_security_service = test_services["login_security_service"]

        is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
            email="new_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )

        assert is_allowed is True
        assert reason is None
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_check_login_allowed_with_failures_below_limit(
        self,
        test_services,
        test_db_session
    ):
        """失敗履歴があっても閾値未満ならログイン許可されるテスト"""
        login_security_service = test_services["login_security_service"]

        for i in range(3):
            await login_security_service.record_login_attempt(
                email="limited_user@example.com",
                ip_address="127.0.0.1",
                user_agent="test-agent",
                is_successful=False,
                db=test_db_session
            )

        is_allowed, reason, retry_after = await login_security_service.check_login_allowed(
            email="limited_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )

        assert is_allowed is True
        assert reason is None
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_get_progressive_delay_no_delay(
        self,
        test_services,
        test_db_session
    ):
        """段階的遅延計算（遅延なし）テスト"""
        login_security_service = test_services["login_security_service"]

        delay = await login_security_service.get_progressive_delay(
            email="no_delay_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )

        assert delay == 0

    @pytest.mark.asyncio
    async def test_get_progressive_delay_with_failures(
        self,
        test_services,
        test_db_session
    ):
        """段階的遅延計算（失敗履歴あり）テスト"""
        login_security_service = test_services["login_security_service"]

        for i in range(2):
            await login_security_service.record_login_attempt(
                email="delay_user@example.com",
                ip_address="127.0.0.1",
                user_agent="test-agent",
                is_successful=False,
                db=test_db_session
            )

        delay = await login_security_service.get_progressive_delay(
            email="delay_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )

        assert delay > 0

    @pytest.mark.asyncio
    async def test_get_lockout_status_empty(
        self,
        test_services,
        test_db_session
    ):
        """ロックアウト状況取得（データなし）テスト"""
        login_security_service = test_services["login_security_service"]

        stats = await login_security_service.get_lockout_status(
            email="nonexistent@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )

        assert stats is not None
        assert stats["email_attempts"] == 0
        assert stats["ip_attempts"] == 0
        assert stats["is_locked"] is False

    @pytest.mark.asyncio
    async def test_get_last_successful_login_with_data(
        self,
        test_services,
        test_db_session
    ):
        """最後の成功ログイン取得テスト"""
        login_security_service = test_services["login_security_service"]

        await login_security_service.record_login_attempt(
            email="stats_user@example.com",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            is_successful=True,
            db=test_db_session
        )
        await login_security_service.record_login_attempt(
            email="stats_user@example.com",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            is_successful=False,
            db=test_db_session
        )

        attempt = await login_security_service.get_last_successful_login(
            email="stats_user@example.com",
            db=test_db_session
        )

        assert attempt is not None
        assert attempt.email == "stats_user@example.com"
        assert attempt.is_successful is True

    @pytest.mark.asyncio
    async def test_cleanup_old_attempts(
        self,
        test_services,
        test_db_session
    ):
        """古いログイン試行のクリーンアップテスト"""
        login_security_service = test_services["login_security_service"]

        cleaned_count = await login_security_service.cleanup_old_attempts(
            days=7,
            db=test_db_session
        )

        assert cleaned_count >= 0
        assert isinstance(cleaned_count, int)
