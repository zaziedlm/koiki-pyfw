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
        user_service.repository.create.return_value = mock_user
        
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
        user_service_without_events.repository.create.return_value = mock_user
        
        with patch('libkoiki.services.user_service.get_password_hash') as mock_get_password_hash:
            mock_get_password_hash.return_value = "hashed_password"
            
            # テスト実行
            result = await user_service_without_events.create_user(user_create_data, mock_db_session)
            
            # 結果検証
            assert result == mock_user
            # イベントパブリッシャーがNoneなのでイベントは発行されない
            assert user_service_without_events.event_publisher is None
    
    async def test_create_user_duplicate_email(
        self,
        user_service,
        user_create_data,
        mock_user,
        mock_db_session
    ):
        """重複メールアドレスでのユーザー作成テスト"""
        # ユーザーリポジトリのモック（既存ユーザーあり）
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = mock_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            # テスト実行（例外を期待）
            with pytest.raises(Exception) as exc_info:
                await user_service.create_user(user_create_data, mock_db_session)
            
            # 結果検証
            assert "already registered" in str(exc_info.value)
            mock_user_repo.get_by_email.assert_called_once_with(
                "test@example.com", mock_db_session
            )
    
    async def test_authenticate_user_success(
        self,
        user_service,
        mock_user,
        mock_db_session
    ):
        """ユーザー認証成功テスト"""
        # ユーザーリポジトリのモック
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = mock_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo), \
             patch('libkoiki.services.user_service.verify_password') as mock_verify_password:
            
            mock_verify_password.return_value = True
            
            # テスト実行
            result = await user_service.authenticate_user(
                email="test@example.com",
                password="TestPass123@",
                db=mock_db_session
            )
            
            # 結果検証
            assert result == mock_user
            mock_user_repo.get_by_email.assert_called_once_with(
                "test@example.com", mock_db_session
            )
            mock_verify_password.assert_called_once_with(
                "TestPass123@", mock_user.hashed_password
            )
    
    async def test_authenticate_user_invalid_email(
        self,
        user_service,
        mock_db_session
    ):
        """無効なメールアドレスでの認証テスト"""
        # ユーザーリポジトリのモック（ユーザーが見つからない）
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = None
        
        with patch.object(user_service, 'user_repository', mock_user_repo), \
             patch('libkoiki.services.user_service.verify_password') as mock_verify_password:
            
            # ダミー認証のモック
            mock_verify_password.return_value = False
            
            # テスト実行
            result = await user_service.authenticate_user(
                email="nonexistent@example.com",
                password="TestPass123@",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is None
            mock_user_repo.get_by_email.assert_called_once_with(
                "nonexistent@example.com", mock_db_session
            )
            # タイミング攻撃対策のためダミー認証が実行される
            mock_verify_password.assert_called_once()
    
    async def test_authenticate_user_invalid_password(
        self,
        user_service,
        mock_user,
        mock_db_session
    ):
        """無効なパスワードでの認証テスト"""
        # ユーザーリポジトリのモック
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = mock_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo), \
             patch('libkoiki.services.user_service.verify_password') as mock_verify_password:
            
            mock_verify_password.return_value = False
            
            # テスト実行
            result = await user_service.authenticate_user(
                email="test@example.com",
                password="wrongpassword",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is None
            mock_user_repo.get_by_email.assert_called_once_with(
                "test@example.com", mock_db_session
            )
            mock_verify_password.assert_called_once_with(
                "wrongpassword", mock_user.hashed_password
            )
    
    async def test_authenticate_user_inactive_user(
        self,
        user_service,
        mock_db_session
    ):
        """非アクティブユーザーの認証テスト"""
        # 非アクティブユーザーのモック
        inactive_user = MagicMock(spec=UserModel)
        inactive_user.is_active = False
        inactive_user.hashed_password = "$2b$12$test_hashed_password"
        
        # ユーザーリポジトリのモック
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = inactive_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo), \
             patch('libkoiki.services.user_service.verify_password') as mock_verify_password:
            
            mock_verify_password.return_value = True
            
            # テスト実行
            result = await user_service.authenticate_user(
                email="test@example.com",
                password="TestPass123@",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is None
            mock_user_repo.get_by_email.assert_called_once_with(
                "test@example.com", mock_db_session
            )
            mock_verify_password.assert_called_once_with(
                "TestPass123@", inactive_user.hashed_password
            )
    
    async def test_get_user_by_id_success(
        self,
        user_service,
        mock_user,
        mock_db_session
    ):
        """ID指定でのユーザー取得成功テスト"""
        # ユーザーリポジトリのモック
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            # テスト実行
            result = await user_service.get_user_by_id(1, mock_db_session)
            
            # 結果検証
            assert result == mock_user
            mock_user_repo.get_by_id.assert_called_once_with(1, mock_db_session)
    
    async def test_get_user_by_id_not_found(
        self,
        user_service,
        mock_db_session
    ):
        """ID指定でのユーザー取得失敗テスト"""
        # ユーザーリポジトリのモック（ユーザーが見つからない）
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = None
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            # テスト実行
            result = await user_service.get_user_by_id(999, mock_db_session)
            
            # 結果検証
            assert result is None
            mock_user_repo.get_by_id.assert_called_once_with(999, mock_db_session)
    
    async def test_get_user_by_email_success(
        self,
        user_service,
        mock_user,
        mock_db_session
    ):
        """メールアドレス指定でのユーザー取得成功テスト"""
        # ユーザーリポジトリのモック
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = mock_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            # テスト実行
            result = await user_service.get_user_by_email("test@example.com", mock_db_session)
            
            # 結果検証
            assert result == mock_user
            mock_user_repo.get_by_email.assert_called_once_with(
                "test@example.com", mock_db_session
            )
