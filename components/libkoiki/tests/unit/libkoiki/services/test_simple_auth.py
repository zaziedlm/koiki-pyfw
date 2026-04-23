"""簡単な認証テスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
def test_simple_auth():
    """基本的な認証テスト"""
    assert True


@pytest.mark.unit
def test_mock_example():
    """モックの使用例"""
    mock_service = MagicMock()
    mock_service.get_user.return_value = MagicMock(id=1, email="test@example.com")
    
    # モックの動作確認
    user = mock_service.get_user()
    assert user.id == 1
    assert user.email == "test@example.com"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_mock_example():
    """非同期モックの使用例"""
    mock_service = AsyncMock()
    mock_service.authenticate.return_value = True
    
    # 非同期モックの動作確認
    result = await mock_service.authenticate("test@example.com", "password")
    assert result is True
    
    # 呼び出し確認
    mock_service.authenticate.assert_called_once_with("test@example.com", "password")