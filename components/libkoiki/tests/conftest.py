import os
import sys

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


LIBKOIKI_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

if LIBKOIKI_SRC not in sys.path:
    sys.path.insert(0, LIBKOIKI_SRC)


@pytest.fixture
def mock_db_session():
    """モック用データベースセッション（libkoiki ユニットテスト向け）"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.scalars = AsyncMock()
    session.scalar = AsyncMock()
    return session
