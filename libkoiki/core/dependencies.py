from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
# async_session_maker の代わりに正しい名前の AsyncSessionFactory をインポート
from libkoiki.db.session import AsyncSessionFactory
from libkoiki.services.user_service import UserService

# データベースセッションの依存性
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    リクエストごとに新しい AsyncSession を提供し、終了時に閉じる
    """
    # session.py ですでに get_db() が実装されているので、そちらを使用することも検討してください
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# UserService の依存性
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    UserService インスタンスを提供
    """
    return UserService(db)

# 依存性注入用のタイプエイリアス
UserServiceDep = Annotated[UserService, Depends(get_user_service)]