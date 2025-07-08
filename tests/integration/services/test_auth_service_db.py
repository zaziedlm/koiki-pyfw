"""認証サービス データベース統合テスト"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from libkoiki.schemas.user import UserCreate
from libkoiki.core.exceptions import ValidationException


@pytest.mark.integration
class TestAuthServiceDatabase:
    """認証サービス データベース統合テスト"""
    
    # ====== トークンペア作成テスト ======
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_token_pair_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """トークンペア作成成功テスト（実際のDB使用）"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            email="auth_token_test@example.com",
            password="TestPass123@",
            full_name="Auth Token Test User"
        )
        
        user_service = test_services["user_service"]
        auth_service = test_services["auth_service"]
        
        # ユーザーを作成
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # トークンペアを作成
        access_token, refresh_token, expires_in = await auth_service.create_token_pair(
            user=created_user,
            db=test_db_session,
            device_info='{"user_agent": "test", "ip_address": "127.0.0.1"}'
        )
        
        # 結果検証
        assert access_token is not None
        assert refresh_token is not None
        assert expires_in > 0
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert isinstance(expires_in, int)
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """リフレッシュトークン成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            email="refresh_token_test@example.com",
            password="TestPass123@",
            full_name="Refresh Token Test User"
        )
        
        user_service = test_services["user_service"]
        auth_service = test_services["auth_service"]
        
        # ユーザーを作成
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # 初回トークンペアを作成
        initial_access_token, initial_refresh_token, _ = await auth_service.create_token_pair(
            user=created_user,
            db=test_db_session,
            device_info='{"user_agent": "test", "ip_address": "127.0.0.1"}'
        )
        
        # リフレッシュトークンを使用して新しいアクセストークンを取得
        result = await auth_service.refresh_access_token(
            refresh_token=initial_refresh_token,
            db=test_db_session
        )
        
        # 結果検証
        assert result is not None
        new_access_token, new_refresh_token, expires_in = result
        assert new_access_token is not None
        assert new_refresh_token is not None
        assert expires_in > 0
        assert new_access_token != initial_access_token  # 新しいアクセストークン
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_token(
        self,
        test_services,
        test_db_session
    ):
        """無効なリフレッシュトークンテスト"""
        auth_service = test_services["auth_service"]
        
        # 無効なリフレッシュトークンでテスト
        result = await auth_service.refresh_access_token(
            refresh_token="invalid_refresh_token",
            db=test_db_session
        )
        
        # 結果検証
        assert result is None
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """ユーザートークン無効化成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            email="revoke_tokens_test@example.com",
            password="TestPass123@",
            full_name="Revoke Tokens Test User"
        )
        
        user_service = test_services["user_service"]
        auth_service = test_services["auth_service"]
        
        # ユーザーを作成
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # 複数のトークンペアを作成
        await auth_service.create_token_pair(
            user=created_user,
            db=test_db_session,
            device_info='{"user_agent": "chrome", "ip_address": "127.0.0.1"}'
        )
        await auth_service.create_token_pair(
            user=created_user,
            db=test_db_session,
            device_info='{"user_agent": "firefox", "ip_address": "127.0.0.1"}'
        )
        
        # ユーザーのトークンを無効化
        revoked_count = await auth_service.revoke_user_tokens(
            user_id=created_user.id,
            db=test_db_session
        )
        
        # 結果検証
        assert revoked_count >= 2  # 2つ以上のトークンが無効化されている
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_get_user_tokens_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """ユーザートークン取得成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            email="get_tokens_test@example.com",
            password="TestPass123@",
            full_name="Get Tokens Test User"
        )
        
        user_service = test_services["user_service"]
        auth_service = test_services["auth_service"]
        
        # ユーザーを作成
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # トークンペアを作成
        await auth_service.create_token_pair(
            user=created_user,
            db=test_db_session,
            device_info='{"user_agent": "test", "ip_address": "127.0.0.1"}'
        )
        
        # ユーザーのトークンを取得
        tokens = await auth_service.get_user_tokens(
            user_id=created_user.id,
            db=test_db_session
        )
        
        # 結果検証
        assert len(tokens) >= 1  # 少なくとも1つのトークンが存在
        assert tokens[0].user_id == created_user.id
        assert tokens[0].is_revoked is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(
        self,
        test_services,
        test_db_session
    ):
        """期限切れトークンクリーンアップテスト"""
        auth_service = test_services["auth_service"]
        
        # 期限切れトークンのクリーンアップを実行
        cleaned_count = await auth_service.cleanup_expired_tokens(test_db_session)
        
        # 結果検証
        assert cleaned_count >= 0  # 0以上の数値が返される
        assert isinstance(cleaned_count, int)