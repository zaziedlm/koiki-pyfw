"""ユーザーサービス データベース統合テスト"""
import pytest
from unittest.mock import patch

from libkoiki.schemas.user import UserCreate, UserUpdate
from libkoiki.core.exceptions import ValidationException


@pytest.mark.integration
class TestUserServiceDatabase:
    """ユーザーサービス データベース統合テスト"""
    
    # ====== ユーザー作成テスト ======
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """ユーザー作成成功テスト（実際のDB使用）"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストデータ
        user_data = UserCreate(
            username="integration_user",
            email="integration_test@example.com",
            password="TestPass123@",
            full_name="Integration Test User"
        )
        
        # テスト実行
        user_service = test_services["user_service"]
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # 結果検証
        assert created_user is not None
        assert created_user.email == "integration_test@example.com"
        assert created_user.full_name == "Integration Test User"
        assert created_user.is_active is True
        assert created_user.is_superuser is False
        assert created_user.id is not None
        
        # パスワードがハッシュ化されていることを確認
        assert created_user.hashed_password != "TestPass123@"
        assert created_user.hashed_password.startswith("$2b$")
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """重複メールアドレスでのユーザー作成テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストデータ
        user_data = UserCreate(
            username="duplicate_user",
            email="duplicate_test@example.com",
            password="TestPass123@",
            full_name="Duplicate Test User"
        )
        
        user_service = test_services["user_service"]
        
        # 最初のユーザーを作成
        await user_service.create_user(user_data, test_db_session)
        
        # 同じメールアドレスで再度作成を試行（例外を期待）
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user(user_data, test_db_session)
        
        # エラーメッセージを確認
        assert "already registered" in str(exc_info.value)
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_weak_password(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """弱いパスワードでのユーザー作成テスト"""
        # モックの設定（弱いパスワード）
        mock_check_password.return_value = False
        
        # テストデータ
        user_data = UserCreate(
            username="weak_password_user",
            email="weak_password@example.com",
            password="weak",
            full_name="Weak Password User"
        )
        
        user_service = test_services["user_service"]
        
        # テスト実行（例外を期待）
        with pytest.raises(ValidationException) as exc_info:
            await user_service.create_user(user_data, test_db_session)
        
        # エラーメッセージを確認
        assert "complexity requirements" in str(exc_info.value)
    
    # ====== ユーザー取得テスト ======
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """メールアドレスでのユーザー取得成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            username="get_test_user",
            email="get_test@example.com",
            password="TestPass123@",
            full_name="Get Test User"
        )
        
        user_service = test_services["user_service"]
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # メールアドレスでユーザーを取得
        retrieved_user = await user_service.get_user_by_email(
            "get_test@example.com", test_db_session
        )
        
        # 結果検証
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "get_test@example.com"
        assert retrieved_user.full_name == "Get Test User"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(
        self,
        test_services,
        test_db_session
    ):
        """存在しないメールアドレスでのユーザー取得テスト"""
        user_service = test_services["user_service"]
        
        # 存在しないメールアドレスでユーザーを取得
        retrieved_user = await user_service.get_user_by_email(
            "nonexistent@example.com", test_db_session
        )
        
        # 結果検証
        assert retrieved_user is None
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """IDでのユーザー取得成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            username="get_id_test_user",
            email="get_id_test@example.com",
            password="TestPass123@",
            full_name="Get ID Test User"
        )
        
        user_service = test_services["user_service"]
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # IDでユーザーを取得
        retrieved_user = await user_service.get_user_by_id(
            created_user.id, test_db_session
        )
        
        # 結果検証
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "get_id_test@example.com"
        assert retrieved_user.full_name == "Get ID Test User"
    
    # ====== ユーザー認証テスト ======
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """ユーザー認証成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            username="auth_test_user",
            email="auth_test@example.com",
            password="TestPass123@",
            full_name="Auth Test User"
        )
        
        user_service = test_services["user_service"]
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # 認証テスト
        authenticated_user = await user_service.authenticate_user(
            email="auth_test@example.com",
            password="TestPass123@",
            db=test_db_session
        )
        
        # 結果検証
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.email == "auth_test@example.com"
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """無効なパスワードでの認証テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            username="auth_invalid_user",
            email="auth_invalid@example.com",
            password="TestPass123@",
            full_name="Auth Invalid User"
        )
        
        user_service = test_services["user_service"]
        await user_service.create_user(user_data, test_db_session)
        
        # 無効なパスワードで認証テスト
        authenticated_user = await user_service.authenticate_user(
            email="auth_invalid@example.com",
            password="WrongPassword123@",
            db=test_db_session
        )
        
        # 結果検証
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(
        self,
        test_services,
        test_db_session
    ):
        """存在しないメールアドレスでの認証テスト"""
        user_service = test_services["user_service"]
        
        # 存在しないメールアドレスで認証テスト
        authenticated_user = await user_service.authenticate_user(
            email="nonexistent@example.com",
            password="TestPass123@",
            db=test_db_session
        )
        
        # 結果検証
        assert authenticated_user is None
    
    # ====== ユーザー更新テスト ======
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_update_user_success(
        self,
        mock_check_password,
        test_services,
        test_db_session
    ):
        """ユーザー更新成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        
        # テストユーザーを作成
        user_data = UserCreate(
            username="update_test_user",
            email="update_test@example.com",
            password="TestPass123@",
            full_name="Update Test User"
        )
        
        user_service = test_services["user_service"]
        created_user = await user_service.create_user(user_data, test_db_session)
        
        # 更新データ
        update_data = UserUpdate(
            full_name="Updated Test User",
            email="updated_test@example.com"
        )
        
        # ユーザー更新
        updated_user = await user_service.update_user(
            user_id=created_user.id,
            user_update=update_data,
            db=test_db_session
        )
        
        # 結果検証
        assert updated_user is not None
        assert updated_user.id == created_user.id
        assert updated_user.full_name == "Updated Test User"
        assert updated_user.email == "updated_test@example.com"
    
    # ====== クリーンアップ用のヘルパー ======
    
    @pytest.mark.asyncio
    async def test_cleanup_test_users(
        self,
        test_services,
        test_db_session
    ):
        """テストユーザーのクリーンアップ"""
        # このテストは他のテストの後に実行され、
        # テストで作成されたユーザーをクリーンアップする
        user_service = test_services["user_service"]
        
        # テストで作成されたユーザーを削除
        test_emails = [
            "integration_test@example.com",
            "duplicate_test@example.com",
            "get_test@example.com",
            "get_id_test@example.com",
            "auth_test@example.com",
            "auth_invalid@example.com",
            "updated_test@example.com"
        ]
        
        for email in test_emails:
            user = await user_service.get_user_by_email(email, test_db_session)
            if user:
                await user_service.delete_user(user.id, test_db_session)
        
        # クリーンアップ完了
        assert True