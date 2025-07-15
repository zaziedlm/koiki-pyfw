"""ログインセキュリティサービス データベース統合テスト"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from libkoiki.schemas.user import UserCreate


@pytest.mark.integration
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
            success=True,
            db=test_db_session
        )
        
        # 結果検証
        assert attempt is not None
        assert attempt.email == "security_test@example.com"
        assert attempt.ip_address == "127.0.0.1"
        assert attempt.user_agent == "test-agent"
        assert attempt.success is True
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
            success=False,
            db=test_db_session
        )
        
        # 結果検証
        assert attempt is not None
        assert attempt.email == "security_fail_test@example.com"
        assert attempt.ip_address == "192.168.1.100"
        assert attempt.success is False
    
    @pytest.mark.asyncio
    async def test_check_login_attempts_no_limit(
        self,
        test_services,
        test_db_session
    ):
        """ログイン試行制限チェック（制限なし）テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 制限チェック（新しいメールアドレス）
        is_limited, remaining_attempts = await login_security_service.check_login_attempts(
            email="new_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )
        
        # 結果検証
        assert is_limited is False
        assert remaining_attempts > 0
    
    @pytest.mark.asyncio
    async def test_check_login_attempts_with_failures(
        self,
        test_services,
        test_db_session
    ):
        """ログイン試行制限チェック（失敗履歴あり）テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 複数の失敗試行を記録
        for i in range(3):
            await login_security_service.record_login_attempt(
                email="limited_user@example.com",
                ip_address="127.0.0.1",
                user_agent="test-agent",
                success=False,
                db=test_db_session
            )
        
        # 制限チェック
        is_limited, remaining_attempts = await login_security_service.check_login_attempts(
            email="limited_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )
        
        # 結果検証
        assert remaining_attempts < 5  # デフォルト制限より少ない
    
    @pytest.mark.asyncio
    async def test_calculate_login_delay_no_delay(
        self,
        test_services,
        test_db_session
    ):
        """ログイン遅延計算（遅延なし）テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 遅延計算（新しいメールアドレス）
        delay = await login_security_service.calculate_login_delay(
            email="no_delay_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )
        
        # 結果検証
        assert delay == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_login_delay_with_failures(
        self,
        test_services,
        test_db_session
    ):
        """ログイン遅延計算（失敗履歴あり）テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 複数の失敗試行を記録
        for i in range(2):
            await login_security_service.record_login_attempt(
                email="delay_user@example.com",
                ip_address="127.0.0.1",
                user_agent="test-agent",
                success=False,
                db=test_db_session
            )
        
        # 遅延計算
        delay = await login_security_service.calculate_login_delay(
            email="delay_user@example.com",
            ip_address="127.0.0.1",
            db=test_db_session
        )
        
        # 結果検証
        assert delay > 0.0  # 遅延が発生
    
    @pytest.mark.asyncio
    async def test_get_login_statistics_empty(
        self,
        test_services,
        test_db_session
    ):
        """ログイン統計取得（データなし）テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 存在しないメールアドレスの統計を取得
        stats = await login_security_service.get_login_statistics(
            email="nonexistent@example.com",
            db=test_db_session
        )
        
        # 結果検証
        assert stats is not None
        assert stats.get("total_attempts", 0) == 0
        assert stats.get("successful_attempts", 0) == 0
        assert stats.get("failed_attempts", 0) == 0
    
    @pytest.mark.asyncio
    async def test_get_login_statistics_with_data(
        self,
        test_services,
        test_db_session
    ):
        """ログイン統計取得（データあり）テスト"""
        login_security_service = test_services["login_security_service"]
        
        # 複数のログイン試行を記録
        await login_security_service.record_login_attempt(
            email="stats_user@example.com",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            success=True,
            db=test_db_session
        )
        await login_security_service.record_login_attempt(
            email="stats_user@example.com",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            success=False,
            db=test_db_session
        )
        
        # 統計を取得
        stats = await login_security_service.get_login_statistics(
            email="stats_user@example.com",
            db=test_db_session
        )
        
        # 結果検証
        assert stats is not None
        assert stats.get("total_attempts", 0) >= 2
        assert stats.get("successful_attempts", 0) >= 1
        assert stats.get("failed_attempts", 0) >= 1
    
    @pytest.mark.asyncio
    async def test_cleanup_old_attempts(
        self,
        test_services,
        test_db_session
    ):
        """古いログイン試行のクリーンアップテスト"""
        login_security_service = test_services["login_security_service"]
        
        # 古いログイン試行をクリーンアップ
        cleaned_count = await login_security_service.cleanup_old_attempts(
            days_old=7,
            db=test_db_session
        )
        
        # 結果検証
        assert cleaned_count >= 0  # 0以上の数値が返される
        assert isinstance(cleaned_count, int)