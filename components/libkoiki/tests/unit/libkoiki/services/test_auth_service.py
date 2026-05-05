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
    
    @patch('libkoiki.services.auth_service.verify_refresh_token_format', return_value=True)
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self,
        mock_verify_format,
        auth_service,
        mock_user,
        mock_db_session
    ):
        """リフレッシュトークンによるアクセストークン更新テスト"""
        # リフレッシュトークンリポジトリのモック
        auth_service.refresh_token_repo.set_session = MagicMock()
        auth_service.refresh_token_repo.get_valid_token = AsyncMock(return_value=MagicMock(
            user_id=1,
            is_valid=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        ))

        # ユーザーリポジトリのモック
        auth_service.user_repo.set_session = MagicMock()
        auth_service.user_repo.get = AsyncMock(return_value=mock_user)

        with patch('libkoiki.core.security.create_access_token', return_value='new_access_token'):
            # テスト実行
            access_token, new_refresh_token, expires_in = await auth_service.refresh_access_token(
                refresh_token="test_refresh_token",
                db=mock_db_session
            )

            # 結果検証
            assert access_token == "new_access_token"
            assert isinstance(expires_in, int)

            # リポジトリが呼び出されたことを確認
            auth_service.refresh_token_repo.set_session.assert_called_once_with(mock_db_session)
            auth_service.refresh_token_repo.get_valid_token.assert_called_once()
    
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
        auth_service.refresh_token_repo.revoke_user_tokens.assert_called_once_with(
            user_id=mock_user.id, exclude_token_id=None
        )
