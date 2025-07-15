"""認証サービス包括的ユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from libkoiki.services.auth_service import AuthService
from libkoiki.models.user import UserModel
from libkoiki.models.refresh_token import RefreshTokenModel
from libkoiki.repositories.refresh_token_repository import RefreshTokenRepository
from libkoiki.repositories.user_repository import UserRepository


@pytest.mark.unit
class TestAuthServiceComprehensive:
    """認証サービス包括的ユニットテスト"""
    
    @pytest.fixture
    def mock_refresh_token_repo(self):
        """モックリフレッシュトークンリポジトリ"""
        repo = AsyncMock(spec=RefreshTokenRepository)
        repo.set_session = MagicMock()
        return repo
    
    @pytest.fixture
    def mock_user_repo(self):
        """モックユーザーリポジトリ"""
        repo = AsyncMock(spec=UserRepository)
        repo.set_session = MagicMock()
        return repo
    
    @pytest.fixture
    def auth_service(self, mock_refresh_token_repo, mock_user_repo):
        """認証サービスのインスタンス"""
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
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    # ====== トークンペア作成テスト ======
    
    @patch('libkoiki.services.auth_service.create_token_pair')
    @patch('libkoiki.services.auth_service.RefreshTokenModel.create_expires_at')
    @pytest.mark.asyncio
    async def test_create_token_pair_success(
        self,
        mock_create_expires_at,
        mock_create_token_pair,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """トークンペア作成成功テスト"""
        # モックの設定
        mock_create_token_pair.return_value = ("access_token", "refresh_token", 3600)
        mock_create_expires_at.return_value = datetime.now(timezone.utc) + timedelta(days=7)
        
        # テスト実行
        access_token, refresh_token, expires_in = await auth_service.create_token_pair(
            user=mock_user,
            db=mock_db_session,
            device_info="test_device_info"
        )
        
        # 結果検証
        assert access_token == "access_token"
        assert refresh_token == "refresh_token"
        assert expires_in == 3600
        
        # リポジトリメソッドが呼び出されたことを確認
        auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
        auth_service.refresh_token_repo.create_refresh_token.assert_called_once()
    
    @patch('libkoiki.services.auth_service.create_token_pair')
    @pytest.mark.asyncio
    async def test_create_token_pair_with_device_info(
        self,
        mock_create_token_pair,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """デバイス情報付きトークンペア作成テスト"""
        # モックの設定
        mock_create_token_pair.return_value = ("access_token", "refresh_token", 3600)
        
        device_info = '{"user_agent": "Mozilla/5.0", "ip_address": "192.168.1.1"}'
        
        # テスト実行
        await auth_service.create_token_pair(
            user=mock_user,
            db=mock_db_session,
            device_info=device_info
        )
        
        # create_token_pairが正しい引数で呼び出されたことを確認
        mock_create_token_pair.assert_called_once_with(mock_user.id, device_info)
    
    @patch('libkoiki.services.auth_service.create_token_pair')
    @pytest.mark.asyncio
    async def test_create_token_pair_repository_error(
        self,
        mock_create_token_pair,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """リポジトリエラー時のトークンペア作成テスト"""
        # モックの設定
        mock_create_token_pair.return_value = ("access_token", "refresh_token", 3600)
        auth_service.refresh_token_repo.create_refresh_token.side_effect = Exception("Database error")
        
        # テスト実行（例外を期待）
        with pytest.raises(Exception) as exc_info:
            await auth_service.create_token_pair(
                user=mock_user,
                db=mock_db_session
            )
        
        # エラーメッセージを確認
        assert "Database error" in str(exc_info.value)
    
    # ====== リフレッシュトークンテスト ======
    
    @patch('libkoiki.services.auth_service.create_token_pair')
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self,
        mock_create_token_pair,
        auth_service,
        mock_user,
        mock_refresh_token,
        mock_db_session
    ):
        """リフレッシュトークン成功テスト"""
        # モックの設定
        mock_create_token_pair.return_value = ("new_access_token", "new_refresh_token", 3600)
        auth_service.refresh_token_repo.get_valid_token.return_value = mock_refresh_token
        auth_service.user_repo.get_by_id.return_value = mock_user
        
        # テスト実行
        access_token, refresh_token, expires_in = await auth_service.refresh_access_token(
            refresh_token="old_refresh_token",
            db=mock_db_session
        )
        
        # 結果検証
        assert access_token == "new_access_token"
        assert refresh_token == "new_refresh_token"
        assert expires_in == 3600
        
        # リポジトリメソッドが呼び出されたことを確認
        auth_service.refresh_token_repo.get_valid_token.assert_called_once_with("old_refresh_token")
        auth_service.user_repo.get_by_id.assert_called_once_with(mock_refresh_token.user_id)
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_token(
        self,
        auth_service,
        mock_db_session
    ):
        """無効なリフレッシュトークンテスト"""
        # モックの設定（無効なトークン）
        auth_service.refresh_token_repo.get_valid_token.return_value = None
        
        # テスト実行
        result = await auth_service.refresh_access_token(
            refresh_token="invalid_token",
            db=mock_db_session
        )
        
        # 結果検証
        assert result is None
        auth_service.refresh_token_repo.get_valid_token.assert_called_once_with("invalid_token")
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_user_not_found(
        self,
        auth_service,
        mock_refresh_token,
        mock_db_session
    ):
        """ユーザーが見つからない場合のリフレッシュトークンテスト"""
        # モックの設定
        auth_service.refresh_token_repo.get_valid_token.return_value = mock_refresh_token
        auth_service.user_repo.get_by_id.return_value = None
        
        # テスト実行
        result = await auth_service.refresh_access_token(
            refresh_token="valid_token",
            db=mock_db_session
        )
        
        # 結果検証
        assert result is None
        auth_service.user_repo.get_by_id.assert_called_once_with(mock_refresh_token.user_id)
    
    @patch('libkoiki.services.auth_service.create_token_pair')
    @pytest.mark.asyncio
    async def test_refresh_access_token_with_rotation(
        self,
        mock_create_token_pair,
        auth_service,
        mock_user,
        mock_refresh_token,
        mock_db_session
    ):
        """トークンローテーション付きリフレッシュテスト"""
        # モックの設定
        mock_create_token_pair.return_value = ("new_access_token", "new_refresh_token", 3600)
        auth_service.refresh_token_repo.get_valid_token.return_value = mock_refresh_token
        auth_service.user_repo.get_by_id.return_value = mock_user
        
        # テスト実行（ローテーション有効）
        access_token, refresh_token, expires_in = await auth_service.refresh_access_token(
            refresh_token="old_refresh_token",
            db=mock_db_session,
            enable_rotation=True
        )
        
        # 結果検証
        assert access_token == "new_access_token"
        assert refresh_token == "new_refresh_token"
        assert expires_in == 3600
        
        # 古いトークンが無効化されることを確認
        auth_service.refresh_token_repo.revoke_token.assert_called_once_with("old_refresh_token")
    
    # ====== ユーザートークン管理テスト ======
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_success(
        self,
        auth_service,
        mock_db_session
    ):
        """ユーザートークン無効化成功テスト"""
        # モックの設定
        auth_service.refresh_token_repo.revoke_user_tokens.return_value = 3
        
        # テスト実行
        revoked_count = await auth_service.revoke_user_tokens(
            user_id=1,
            db=mock_db_session
        )
        
        # 結果検証
        assert revoked_count == 3
        auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
        auth_service.refresh_token_repo.revoke_user_tokens.assert_called_once_with(1, None)
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_with_exclusion(
        self,
        auth_service,
        mock_db_session
    ):
        """特定トークンを除外したユーザートークン無効化テスト"""
        # モックの設定
        auth_service.refresh_token_repo.revoke_user_tokens.return_value = 2
        
        # テスト実行
        revoked_count = await auth_service.revoke_user_tokens(
            user_id=1,
            db=mock_db_session,
            exclude_token_id=5
        )
        
        # 結果検証
        assert revoked_count == 2
        auth_service.refresh_token_repo.revoke_user_tokens.assert_called_once_with(1, 5)
    
    @pytest.mark.asyncio
    async def test_get_user_tokens_success(
        self,
        auth_service,
        mock_refresh_token,
        mock_db_session
    ):
        """ユーザートークン取得成功テスト"""
        # モックの設定
        auth_service.refresh_token_repo.get_user_tokens.return_value = [mock_refresh_token]
        
        # テスト実行
        tokens = await auth_service.get_user_tokens(
            user_id=1,
            db=mock_db_session
        )
        
        # 結果検証
        assert len(tokens) == 1
        assert tokens[0] == mock_refresh_token
        auth_service.refresh_token_repo.get_user_tokens.assert_called_once_with(1, True)
    
    @pytest.mark.asyncio
    async def test_get_user_tokens_include_revoked(
        self,
        auth_service,
        mock_refresh_token,
        mock_db_session
    ):
        """無効化されたトークンも含むユーザートークン取得テスト"""
        # モックの設定
        auth_service.refresh_token_repo.get_user_tokens.return_value = [mock_refresh_token]
        
        # テスト実行
        tokens = await auth_service.get_user_tokens(
            user_id=1,
            db=mock_db_session,
            only_valid=False
        )
        
        # 結果検証
        assert len(tokens) == 1
        auth_service.refresh_token_repo.get_user_tokens.assert_called_once_with(1, False)
    
    # ====== クリーンアップテスト ======
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(
        self,
        auth_service,
        mock_db_session
    ):
        """期限切れトークンクリーンアップ成功テスト"""
        # モックの設定
        auth_service.refresh_token_repo.cleanup_expired_tokens.return_value = 5
        
        # テスト実行
        cleaned_count = await auth_service.cleanup_expired_tokens(mock_db_session)
        
        # 結果検証
        assert cleaned_count == 5
        auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
        auth_service.refresh_token_repo.cleanup_expired_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_tokens(
        self,
        auth_service,
        mock_db_session
    ):
        """期限切れトークンが存在しない場合のクリーンアップテスト"""
        # モックの設定
        auth_service.refresh_token_repo.cleanup_expired_tokens.return_value = 0
        
        # テスト実行
        cleaned_count = await auth_service.cleanup_expired_tokens(mock_db_session)
        
        # 結果検証
        assert cleaned_count == 0
        auth_service.refresh_token_repo.cleanup_expired_tokens.assert_called_once()
    
    # ====== エラーハンドリングテスト ======
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_repository_error(
        self,
        auth_service,
        mock_db_session
    ):
        """リポジトリエラー時のクリーンアップテスト"""
        # モックの設定
        auth_service.refresh_token_repo.cleanup_expired_tokens.side_effect = Exception("Database error")
        
        # テスト実行（例外を期待）
        with pytest.raises(Exception) as exc_info:
            await auth_service.cleanup_expired_tokens(mock_db_session)
        
        # エラーメッセージを確認
        assert "Database error" in str(exc_info.value)
    
    # ====== 設定テスト ======
    
    @pytest.mark.asyncio
    async def test_service_initialization(
        self,
        mock_refresh_token_repo,
        mock_user_repo
    ):
        """サービス初期化テスト"""
        # テスト実行
        service = AuthService(mock_refresh_token_repo, mock_user_repo)
        
        # 結果検証
        assert service.refresh_token_repo == mock_refresh_token_repo
        assert service.user_repo == mock_user_repo
    
    def test_service_initialization_with_none_repos(self):
        """None リポジトリでの初期化テスト"""
        # テスト実行（例外を期待）
        with pytest.raises(TypeError):
            AuthService(None, None)