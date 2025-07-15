"""認証サービスユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from libkoiki.services.auth_service import AuthService
from libkoiki.models.user import UserModel
from libkoiki.models.refresh_token import RefreshTokenModel


@pytest.mark.unit
class TestAuthService:
    """認証サービスユニットテスト"""
    
    @pytest.fixture
    def auth_service(self):
        """認証サービスのインスタンス"""
        # モックリポジトリを作成
        mock_refresh_token_repo = AsyncMock()
        mock_user_repo = AsyncMock()
        return AuthService(mock_refresh_token_repo, mock_user_repo)
    
    @pytest.fixture
    def mock_user(self):
        """モックユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        user.is_superuser = False
        return user
    
    @pytest.fixture
    def mock_refresh_token(self):
        """モックリフレッシュトークン"""
        token = MagicMock(spec=RefreshTokenModel)
        token.id = 1
        token.user_id = 1
        token.token_hash = "test_token_hash"
        token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token.is_revoked = False
        token.device_info = '{"user_agent": "test", "ip_address": "127.0.0.1"}'
        token.is_valid = True
        return token
    
    @patch('libkoiki.services.auth_service.create_token_pair')
    @pytest.mark.asyncio
    async def test_create_token_pair_success(
        self, 
        mock_create_token_pair,
        auth_service, 
        mock_user, 
        mock_db_session
    ):
        """トークンペア作成成功テスト"""
        # モックの設定
        mock_create_token_pair.return_value = ("test_access_token", "test_refresh_token", 3600)
        
        # リフレッシュトークンリポジトリのモック
        auth_service.refresh_token_repo.set_session = MagicMock()
        auth_service.refresh_token_repo.create_refresh_token = AsyncMock()
        
        # テスト実行
        access_token, refresh_token, expires_in = await auth_service.create_token_pair(
            user=mock_user,
            db=mock_db_session,
            device_info="test_device_info"
        )
        
        # 結果検証
        assert access_token == "test_access_token"
        assert refresh_token == "test_refresh_token"
        assert expires_in == 3600  # 1時間
        
        # リポジトリが呼び出されたことを確認
        auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
        auth_service.refresh_token_repo.create_refresh_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """リフレッシュトークンによるアクセストークン更新テスト"""
        # リフレッシュトークンリポジトリのモック
        auth_service.refresh_token_repo.set_session = MagicMock()
        auth_service.refresh_token_repo.get_valid_refresh_token = AsyncMock(return_value=MagicMock(
            user_id=1,
            is_valid=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        ))
        
        # ユーザーリポジトリのモック
        auth_service.user_repo.set_session = MagicMock()
        auth_service.user_repo.get_by_id = AsyncMock(return_value=mock_user)
        
        with patch('libkoiki.services.auth_service.create_token_pair') as mock_create_token_pair:
            mock_create_token_pair.return_value = ("new_access_token", "new_refresh_token", 3600)
            
            # テスト実行
            access_token, refresh_token, expires_in = await auth_service.refresh_access_token(
                refresh_token="test_refresh_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert access_token == "new_access_token"
            assert refresh_token == "new_refresh_token"
            assert expires_in == 3600
            
            # リポジトリが呼び出されたことを確認
            auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
            auth_service.refresh_token_repo.get_valid_refresh_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_success(
        self,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """ユーザートークン無効化成功テスト"""
        # リフレッシュトークンリポジトリのモック
        auth_service.refresh_token_repo.set_session = MagicMock()
        auth_service.refresh_token_repo.revoke_user_tokens = AsyncMock(return_value=3)
        
        # テスト実行
        result = await auth_service.revoke_user_tokens(
            user_id=mock_user.id,
            db=mock_db_session
        )
        
        # 結果検証
        assert result == 3
        auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
        auth_service.refresh_token_repo.revoke_user_tokens.assert_called_once_with(mock_user.id)
    
    @patch('libkoiki.services.auth_service.verify_token')
    async def test_verify_access_token_user_not_found(
        self,
        mock_verify_token,
        auth_service,
        mock_db_session
    ):
        """ユーザーが見つからない場合のテスト"""
        # モックの設定
        mock_verify_token.return_value = {"sub": "999", "exp": 1234567890}
        
        # ユーザーリポジトリのモック（ユーザーが見つからない）
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = None
        
        with patch.object(auth_service, 'user_repository', mock_user_repo):
            # テスト実行
            user = await auth_service.verify_access_token(
                token="test_access_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert user is None
            mock_user_repo.get_by_id.assert_called_once_with(999, mock_db_session)
    
    async def test_refresh_access_token_success(
        self,
        auth_service,
        mock_user,
        mock_refresh_token,
        mock_db_session
    ):
        """リフレッシュトークンによるアクセストークン更新テスト"""
        # リフレッシュトークンリポジトリのモック
        mock_refresh_token_repo = AsyncMock()
        mock_refresh_token_repo.get_by_token.return_value = mock_refresh_token
        
        # ユーザーリポジトリのモック
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_user
        
        with patch.object(auth_service, 'refresh_token_repository', mock_refresh_token_repo), \
             patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch('libkoiki.services.auth_service.create_access_token') as mock_create_token:
            
            mock_create_token.return_value = "new_access_token"
            
            # テスト実行
            access_token, expires_in = await auth_service.refresh_access_token(
                refresh_token="test_refresh_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert access_token == "new_access_token"
            assert expires_in == 3600
            
            # リポジトリが呼び出されたことを確認
            mock_refresh_token_repo.get_by_token.assert_called_once_with(
                "test_refresh_token", mock_db_session
            )
            mock_user_repo.get_by_id.assert_called_once_with(1, mock_db_session)
    
    async def test_refresh_access_token_invalid_token(
        self,
        auth_service,
        mock_db_session
    ):
        """無効なリフレッシュトークンでのテスト"""
        # リフレッシュトークンリポジトリのモック（トークンが見つからない）
        mock_refresh_token_repo = AsyncMock()
        mock_refresh_token_repo.get_by_token.return_value = None
        
        with patch.object(auth_service, 'refresh_token_repository', mock_refresh_token_repo):
            # テスト実行
            result = await auth_service.refresh_access_token(
                refresh_token="invalid_refresh_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is None
            mock_refresh_token_repo.get_by_token.assert_called_once_with(
                "invalid_refresh_token", mock_db_session
            )
    
    async def test_refresh_access_token_expired_token(
        self,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """期限切れリフレッシュトークンでのテスト"""
        # 期限切れのリフレッシュトークン
        expired_token = MagicMock(spec=RefreshTokenModel)
        expired_token.is_valid = False
        
        # リフレッシュトークンリポジトリのモック
        mock_refresh_token_repo = AsyncMock()
        mock_refresh_token_repo.get_by_token.return_value = expired_token
        
        with patch.object(auth_service, 'refresh_token_repository', mock_refresh_token_repo):
            # テスト実行
            result = await auth_service.refresh_access_token(
                refresh_token="expired_refresh_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is None
    
    async def test_revoke_refresh_token_success(
        self,
        auth_service,
        mock_refresh_token,
        mock_db_session
    ):
        """リフレッシュトークン無効化成功テスト"""
        # リフレッシュトークンリポジトリのモック
        mock_refresh_token_repo = AsyncMock()
        mock_refresh_token_repo.get_by_token.return_value = mock_refresh_token
        
        with patch.object(auth_service, 'refresh_token_repository', mock_refresh_token_repo):
            # テスト実行
            result = await auth_service.revoke_refresh_token(
                refresh_token="test_refresh_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is True
            mock_refresh_token_repo.get_by_token.assert_called_once_with(
                "test_refresh_token", mock_db_session
            )
            mock_refresh_token.revoke.assert_called_once()
    
    async def test_revoke_refresh_token_not_found(
        self,
        auth_service,
        mock_db_session
    ):
        """存在しないリフレッシュトークンの無効化テスト"""
        # リフレッシュトークンリポジトリのモック（トークンが見つからない）
        mock_refresh_token_repo = AsyncMock()
        mock_refresh_token_repo.get_by_token.return_value = None
        
        with patch.object(auth_service, 'refresh_token_repository', mock_refresh_token_repo):
            # テスト実行
            result = await auth_service.revoke_refresh_token(
                refresh_token="nonexistent_refresh_token",
                db=mock_db_session
            )
            
            # 結果検証
            assert result is False