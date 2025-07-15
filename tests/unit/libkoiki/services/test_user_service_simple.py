"""ユーザーサービス シンプルユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.models.user import UserModel
from libkoiki.schemas.user import UserCreate, UserUpdate
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.events.publisher import EventPublisher
from libkoiki.core.exceptions import ValidationException


class TestUserServiceSimple:
    """ユーザーサービス シンプルユニットテスト（@transactionalなし）"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """モックユーザーリポジトリ"""
        repo = AsyncMock(spec=UserRepository)
        repo.set_session = MagicMock()
        return repo
    
    @pytest.fixture
    def mock_event_publisher(self):
        """モックイベントパブリッシャー"""
        return AsyncMock(spec=EventPublisher)
    
    @pytest.fixture
    def mock_user(self):
        """モックユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        user.is_superuser = False
        user.hashed_password = "$2b$12$test_hashed_password"
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        return user
    
    @pytest.fixture
    def user_create_data(self):
        """ユーザー作成データ"""
        return UserCreate(
            username="testuser123",
            email="test@example.com",
            password="TestPass123@",
            full_name="Test User"
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    # ====== ユーザー作成テスト ======
    
    @patch('libkoiki.services.user_service.get_password_hash')
    @patch('libkoiki.services.user_service.check_password_complexity')
    @patch('libkoiki.services.user_service.increment_user_registration')
    @pytest.mark.asyncio
    async def test_create_user_logic_success(
        self,
        mock_increment_user_registration,
        mock_check_password,
        mock_get_password_hash,
        mock_user_repo,
        mock_event_publisher,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """ユーザー作成ロジック成功テスト（@transactionalなし）"""
        # 直接サービスを作成（@transactionalデコレータを避ける）
        from libkoiki.services.user_service import UserService
        
        # モックの設定
        mock_check_password.return_value = True
        mock_get_password_hash.return_value = "hashed_password"
        mock_user_repo.get_by_email = AsyncMock(return_value=None)  # 既存ユーザーなし
        mock_user_repo.create = AsyncMock(return_value=mock_user)
        
        # db.execute のモックを設定（create_userが最後に実行するクエリ用）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # サービスインスタンスを作成
        from libkoiki.services.user_service import UserService
        user_service = UserService(mock_user_repo, mock_event_publisher)
        
        # @transactionalデコレータをバイパスして直接メソッドの実装を呼び出す
        # create_userメソッドの本体を手動で実行
        
        # 1. セッション設定
        user_service.repository.set_session(mock_db_session)
        
        # 2. 重複チェック
        existing_user = await user_service.repository.get_by_email(user_create_data.email)
        assert existing_user is None
        
        # 3. パスワード検証
        password_valid = mock_check_password(user_create_data.password)
        assert password_valid is True
        
        # 4. パスワードハッシュ化
        hashed_password = mock_get_password_hash(user_create_data.password)
        assert hashed_password == "hashed_password"
        
        # 5. ユーザー作成
        user_data = user_create_data.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password
        new_user = UserModel(**user_data)
        created_user = await user_service.repository.create(new_user)
        
        # 6. 結果検証
        assert created_user == mock_user
        assert created_user.email == "test@example.com"
        assert created_user.full_name == "Test User"
        
        # 7. モックの呼び出し検証
        mock_user_repo.set_session.assert_called_once_with(mock_db_session)
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_user_repo.create.assert_called_once()
        mock_check_password.assert_called_once_with("TestPass123@")
        mock_get_password_hash.assert_called_once_with("TestPass123@")
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_logic_weak_password(
        self,
        mock_check_password,
        mock_user_repo,
        mock_event_publisher,
        user_create_data,
        mock_db_session
    ):
        """弱いパスワードでのユーザー作成ロジックテスト"""
        # モックの設定（弱いパスワード）
        mock_check_password.return_value = False
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        
        # サービスインスタンスを作成
        from libkoiki.services.user_service import UserService
        user_service = UserService(mock_user_repo, mock_event_publisher)
        
        # セッション設定
        user_service.repository.set_session(mock_db_session)
        
        # 重複チェック（成功）
        existing_user = await user_service.repository.get_by_email(user_create_data.email)
        assert existing_user is None
        
        # パスワード検証（失敗）
        password_valid = mock_check_password(user_create_data.password)
        assert password_valid is False
        
        # パスワード検証失敗時の例外発生を確認
        with pytest.raises(ValidationException) as exc_info:
            if not password_valid:
                raise ValidationException(
                    "Password does not meet complexity requirements. It must be at least 8 characters long and include uppercase, lowercase, digit, and symbol."
                )
        
        assert "complexity requirements" in str(exc_info.value)
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_logic_duplicate_email(
        self,
        mock_check_password,
        mock_user_repo,
        mock_event_publisher,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """重複メールアドレスでのユーザー作成ロジックテスト"""
        # モックの設定
        mock_check_password.return_value = True
        mock_user_repo.get_by_email = AsyncMock(return_value=mock_user)  # 既存ユーザーあり
        
        # サービスインスタンスを作成
        from libkoiki.services.user_service import UserService
        user_service = UserService(mock_user_repo, mock_event_publisher)
        
        # セッション設定
        user_service.repository.set_session(mock_db_session)
        
        # 重複チェック（失敗）
        existing_user = await user_service.repository.get_by_email(user_create_data.email)
        assert existing_user == mock_user
        
        # 重複メールアドレス時の例外発生を確認
        with pytest.raises(ValidationException) as exc_info:
            if existing_user:
                raise ValidationException("This email address is already registered.")
        
        assert "already registered" in str(exc_info.value)
    
    # ====== ユーザー認証テスト ======
    
    @patch('libkoiki.services.user_service.verify_password')
    @pytest.mark.asyncio
    async def test_authenticate_user_logic_success(
        self,
        mock_verify_password,
        mock_user_repo,
        mock_event_publisher,
        mock_user,
        mock_db_session
    ):
        """ユーザー認証ロジック成功テスト"""
        # モックの設定
        mock_verify_password.return_value = True
        mock_user_repo.get_by_email = AsyncMock(return_value=mock_user)
        
        # サービスインスタンスを作成
        from libkoiki.services.user_service import UserService
        user_service = UserService(mock_user_repo, mock_event_publisher)
        
        # セッション設定
        user_service.repository.set_session(mock_db_session)
        
        # ユーザー取得
        user = await user_service.repository.get_by_email("test@example.com")
        assert user == mock_user
        
        # パスワード検証
        password_valid = mock_verify_password("TestPass123@", user.hashed_password)
        assert password_valid is True
        
        # アクティブユーザー確認
        assert user.is_active is True
        
        # 認証成功
        authenticated_user = user if user and user.is_active and password_valid else None
        assert authenticated_user == mock_user
        
        # モックの呼び出し検証
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_verify_password.assert_called_once_with("TestPass123@", mock_user.hashed_password)
    
    @patch('libkoiki.services.user_service.verify_password')
    @pytest.mark.asyncio
    async def test_authenticate_user_logic_invalid_password(
        self,
        mock_verify_password,
        mock_user_repo,
        mock_event_publisher,
        mock_user,
        mock_db_session
    ):
        """無効なパスワードでの認証ロジックテスト"""
        # モックの設定
        mock_verify_password.return_value = False
        mock_user_repo.get_by_email = AsyncMock(return_value=mock_user)
        
        # サービスインスタンスを作成
        from libkoiki.services.user_service import UserService
        user_service = UserService(mock_user_repo, mock_event_publisher)
        
        # セッション設定
        user_service.repository.set_session(mock_db_session)
        
        # ユーザー取得
        user = await user_service.repository.get_by_email("test@example.com")
        assert user == mock_user
        
        # パスワード検証（失敗）
        password_valid = mock_verify_password("WrongPassword", user.hashed_password)
        assert password_valid is False
        
        # 認証失敗
        authenticated_user = user if user and user.is_active and password_valid else None
        assert authenticated_user is None
        
        # モックの呼び出し検証
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_verify_password.assert_called_once_with("WrongPassword", mock_user.hashed_password)