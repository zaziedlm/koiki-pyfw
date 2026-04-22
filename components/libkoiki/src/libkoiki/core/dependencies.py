from typing import Annotated
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession
# session.pyから実装済みのget_db関数をインポート
from libkoiki.db.session import get_db
from libkoiki.services.user_service import UserService

# データベースセッションの依存性はsession.pyから直接インポート済み

# UserService の依存性
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    UserService インスタンスを提供
    """
    from libkoiki.repositories.user_repository import UserRepository
    repository = UserRepository()
    repository.set_session(db)
    return UserService(repository)

# 依存性注入用のタイプエイリアス
UserServiceDep = Annotated[UserService, Depends(get_user_service)]