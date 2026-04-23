"""ユーザーサービス包括的ユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.services.user_service import UserService
from libkoiki.models.user import UserModel
from libkoiki.schemas.user import UserCreate, UserUpdate
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.events.publisher import EventPublisher

# テスト用のシンプルなデコレータ（@transactionalをバイパス）
def simple_transactional(func):
    """テスト用の@transactionalデコレータバイパス"""
    return func


@pytest.mark.unit
@patch('libkoiki.services.user_service.transactional', simple_transactional)
class TestUserService:
    """ユーザーサービス包括的ユニットテスト"""
    
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
    def user_service(self, mock_user_repo, mock_event_publisher):
        """ユーザーサービスのインスタンス"""
        return UserService(mock_user_repo, mock_event_publisher)
    
    @pytest.fixture
    def user_service_without_events(self, mock_user_repo):
        """イベントなしのユーザーサービス"""
        return UserService(mock_user_repo)
    
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
            username="testuser",
            email="test@example.com",
            password="TestPass123@",
            full_name="Test User"
        )
    
    @pytest.fixture
    def user_update_data(self):
        """ユーザー更新データ"""
        return UserUpdate(
            full_name="Updated User",
            email="updated@example.com"
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション - シンプル版"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    # ====== ユーザー作成テスト ======
    
    @patch('libkoiki.services.user_service.get_password_hash')
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        mock_check_password,
        mock_get_password_hash,
        user_service,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """ユーザー作成成功テスト"""
        # モックの設定
        mock_check_password.return_value = True
        mock_get_password_hash.return_value = "hashed_password"
        user_service.repository.get_by_email = AsyncMock(return_value=None)  # 既存ユーザーなし
        user_service.repository.get_by_username = AsyncMock(return_value=None)  # 既存ユーザー名なし
        user_service.repository.create = AsyncMock(return_value=mock_user)
        
        # db.execute のモックを設定（create_userが最後に実行するクエリ用）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # テスト実行
        result = await user_service.create_user(user_create_data, mock_db_session)
        
        # 結果検証
        assert result == mock_user
        user_service.repository.set_session.assert_called_once_with(mock_db_session)
        user_service.repository.get_by_email.assert_called_once_with("test@example.com")
        user_service.repository.create.assert_called_once()
        mock_check_password.assert_called_once_with("TestPass123@")
        mock_get_password_hash.assert_called_once_with("TestPass123@")
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_weak_password(
        self,
        mock_check_password,
        user_service,
        user_create_data,
        mock_db_session
    ):
        """弱いパスワードでのユーザー作成テスト"""
        # メール・ユーザー名チェックをパスさせる
        user_service.repository.get_by_email.return_value = None
        user_service.repository.get_by_username.return_value = None
        # モックの設定（弱いパスワード）
        mock_check_password.return_value = False
        
        # テスト実行（例外を期待）
        with pytest.raises(Exception) as exc_info:
            await user_service.create_user(user_create_data, mock_db_session)
        
        # エラーメッセージを確認
        assert "complexity requirements" in str(exc_info.value)
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        mock_check_password,
        user_service,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """重複メールアドレスでのユーザー作成テスト"""
        # モックの設定
        mock_check_password.return_value = True
        user_service.repository.get_by_email.return_value = mock_user  # 既存ユーザーあり
        
        # テスト実行（例外を期待）
        with pytest.raises(Exception) as exc_info:
            await user_service.create_user(user_create_data, mock_db_session)
        
        # エラーメッセージを確認
        assert "already registered" in str(exc_info.value)
    
    @patch('libkoiki.services.user_service.get_password_hash')
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_with_events(
        self,
        mock_check_password,
        mock_get_password_hash,
        user_service,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """イベント付きユーザー作成テスト"""
        # モックの設定
        mock_check_password.return_value = True
        mock_get_password_hash.return_value = "hashed_password"
        user_service.repository.get_by_email.return_value = None
        user_service.repository.get_by_username.return_value = None
        user_service.repository.create.return_value = mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # テスト実行
        result = await user_service.create_user(user_create_data, mock_db_session)

        # 結果検証
        assert result == mock_user
        # イベントが発行されたことを確認
        user_service.event_publisher.publish.assert_called_once()
    
    @patch('libkoiki.services.user_service.check_password_complexity')
    @pytest.mark.asyncio
    async def test_create_user_without_events(
        self,
        mock_check_password,
        user_service_without_events,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """イベントなしユーザー作成テスト"""
        # モックの設定
        mock_check_password.return_value = True
        user_service_without_events.repository.get_by_email.return_value = None
        user_service_without_events.repository.get_by_username.return_value = None
        user_service_without_events.repository.create.return_value = mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch('libkoiki.services.user_service.get_password_hash') as mock_get_password_hash:
            mock_get_password_hash.return_value = "hashed_password"

            # テスト実行
            result = await user_service_without_events.create_user(user_create_data, mock_db_session)
            
            # 結果検証
            assert result == mock_user
            # イベントパブリッシャーがNoneなのでイベントは発行されない
            assert user_service_without_events.event_publisher is None
