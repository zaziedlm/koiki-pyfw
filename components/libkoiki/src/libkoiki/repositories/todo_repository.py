# src/repositories/todo_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update as sql_update # count用、楽観ロック用のアトミックUPDATE

from libkoiki.models.todo import TodoModel
from libkoiki.repositories.base import BaseRepository
from libkoiki.schemas.todo import TodoCreate, TodoUpdate # スキーマは通常サービス層で使う
import structlog

logger = structlog.get_logger(__name__)

class TodoRepository(BaseRepository[TodoModel, TodoCreate, TodoUpdate]):
    """ToDoリポジトリ実装"""

    def __init__(self):
        """コンストラクタでToDoモデルを指定"""
        super().__init__(TodoModel)

    async def get_multi_by_owner(
        self, owner_id: int, *, skip: int = 0, limit: int = 100
    ) -> Sequence[TodoModel]:
        """特定の所有者のToDoリストを取得します (ページネーション対応)"""
        logger.debug(f"Getting todos for owner", owner_id=owner_id, skip=skip, limit=limit)
        stmt = (
            select(self.model)
            .where(self.model.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc()) # 作成日時の降順でソート
        )
        result = await self.db.execute(stmt)
        todos = result.scalars().all()
        # logger.debug(f"Found {len(todos)} todos for owner", owner_id=owner_id)
        return todos

    async def get_by_id_and_owner(
        self, todo_id: int, owner_id: int
    ) -> Optional[TodoModel]:
        """ToDo ID と 所有者 ID の両方に一致するToDoを取得します"""
        logger.debug(f"Getting todo by id and owner", todo_id=todo_id, owner_id=owner_id)
        stmt = select(self.model).where(
            self.model.id == todo_id,
            self.model.owner_id == owner_id
        )
        result = await self.db.execute(stmt)
        instance = result.scalar_one_or_none()
        # if instance is None:
        #      logger.debug("Todo not found by id and owner", todo_id=todo_id, owner_id=owner_id)
        return instance

    async def apply_versioned_update(
        self, todo_id: int, owner_id: int, expected_version: int, update_data: Dict[str, Any]
    ) -> int:
        """`expected_version` が現在のDB上のversionと一致する場合のみ更新し、versionを+1する。
        一致しなければ何も更新せず0を返す(他リクエストによる競合、または存在しない)。"""
        stmt = (
            sql_update(self.model)
            .where(
                self.model.id == todo_id,
                self.model.owner_id == owner_id,
                self.model.version == expected_version,
            )
            .values(
                version=expected_version + 1,
                updated_at=datetime.now(timezone.utc),
                **update_data,
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def count_by_owner(self, owner_id: int) -> int:
        """特定の所有者のToDo総数を取得します"""
        logger.debug(f"Counting todos for owner", owner_id=owner_id)
        stmt = select(func.count(self.model.id)).where(self.model.owner_id == owner_id)
        result = await self.db.execute(stmt)
        count = result.scalar_one()
        # logger.debug(f"Found {count} todos for owner", owner_id=owner_id)
        return count

    # create, update, delete は BaseRepository のものを使用
