# src/services/todo_service.py
from typing import List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from libkoiki.models.todo import TodoModel
from libkoiki.repositories.todo_repository import TodoRepository
from libkoiki.schemas.todo import TodoCreate, TodoUpdate
from libkoiki.core.exceptions import ResourceNotFoundException, AuthorizationException
from libkoiki.core.transaction import transactional # トランザクションデコレータ

logger = structlog.get_logger(__name__)

class TodoService:
    """ToDoアイテムに関連するビジネスロジックを処理するサービスクラス"""
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    @transactional
    async def create_todo(self, todo_in: TodoCreate, owner_id: int, db: AsyncSession) -> TodoModel:
        """
        新しいToDoアイテムを作成します。

        Args:
            todo_in: 作成するToDoのデータ (Pydanticスキーマ)。
            owner_id: ToDoを所有するユーザーのID。
            db: データベースセッション (transactionalデコレータから注入)。

        Returns:
            作成されたToDoのORMモデルインスタンス。
        """
        logger.info("Service: Creating todo", owner_id=owner_id, title=todo_in.title)
        self.repository.set_session(db) # リポジトリにセッションを設定

        todo_data = todo_in.dict()
        todo_data['owner_id'] = owner_id # 所有者IDを設定
        new_todo = TodoModel(**todo_data) # ORMモデルインスタンスを作成

        created_todo = await self.repository.create(new_todo)
        logger.info("Service: Todo created successfully", todo_id=created_todo.id, owner_id=owner_id)
        # TODO: イベント発行 (例: todo_created)
        return created_todo

    # 読み取り操作は通常トランザクション不要だが、一貫性が必要な場合は @transactional を付与
    async def get_todos_by_owner(
        self, owner_id: int, skip: int, limit: int, db: AsyncSession # 読み取りでもセッションは必要
    ) -> Sequence[TodoModel]:
        """指定された所有者のToDoリストを取得します"""
        logger.debug("Service: Getting todos by owner", owner_id=owner_id, skip=skip, limit=limit)
        self.repository.set_session(db)
        return await self.repository.get_multi_by_owner(owner_id=owner_id, skip=skip, limit=limit)

    async def get_todo_by_id(self, todo_id: int, owner_id: int, db: AsyncSession) -> TodoModel:
        """
        指定されたIDのToDoを取得します。所有者チェックも行います。

        Raises:
            ResourceNotFoundException: ToDoが見つからない場合。
            AuthorizationException: 所有者でない場合 (リポジトリレベルでチェックされる)。
        """
        logger.debug("Service: Getting todo by id", todo_id=todo_id, owner_id=owner_id)
        self.repository.set_session(db)
        # リポジトリメソッドで所有者もチェックする
        todo = await self.repository.get_by_id_and_owner(todo_id=todo_id, owner_id=owner_id)
        if not todo:
            # 見つからない場合、存在しないか権限がないかのどちらか
            # 存在確認だけ別途行うことも可能だが、ここでは区別しない
            logger.warning("Service: Todo not found or access denied", todo_id=todo_id, owner_id=owner_id)
            raise ResourceNotFoundException(resource_name="ToDo", resource_id=todo_id)
        return todo

    @transactional
    async def update_todo(
        self, todo_id: int, todo_in: TodoUpdate, owner_id: int, db: AsyncSession
    ) -> TodoModel:
        """
        ToDoアイテムを更新します。所有者チェックも行います。

        Raises:
            ResourceNotFoundException: ToDoが見つからない場合。
            AuthorizationException: 所有者でない場合。
        """
        logger.info("Service: Updating todo", todo_id=todo_id, owner_id=owner_id, data=todo_in.dict(exclude_unset=True))
        self.repository.set_session(db)

        # まず、更新対象のToDoが存在し、かつ所有者であることを確認
        db_todo = await self.repository.get_by_id_and_owner(todo_id=todo_id, owner_id=owner_id)
        if not db_todo:
            logger.warning("Service: Todo not found or access denied for update", todo_id=todo_id, owner_id=owner_id)
            # 存在しないか権限がないか
            raise ResourceNotFoundException(resource_name="ToDo", resource_id=todo_id)
            # raise AuthorizationException("You are not authorized to update this ToDo.")

        # BaseRepository の update メソッドを使用
        updated_todo = await self.repository.update(db_obj=db_todo, obj_in=todo_in)
        logger.info("Service: Todo updated successfully", todo_id=todo_id, owner_id=owner_id)
        # TODO: イベント発行 (例: todo_updated)
        return updated_todo

    @transactional
    async def delete_todo(self, todo_id: int, owner_id: int, db: AsyncSession) -> None:
        """
        ToDoアイテムを削除します。所有者チェックも行います。

        Raises:
            ResourceNotFoundException: ToDoが見つからない場合。
            AuthorizationException: 所有者でない場合。
        """
        logger.info("Service: Deleting todo", todo_id=todo_id, owner_id=owner_id)
        self.repository.set_session(db)

        # 削除対象が存在し、かつ所有者であることを確認
        db_todo = await self.repository.get_by_id_and_owner(todo_id=todo_id, owner_id=owner_id)
        if not db_todo:
            logger.warning("Service: Todo not found or access denied for deletion", todo_id=todo_id, owner_id=owner_id)
            raise ResourceNotFoundException(resource_name="ToDo", resource_id=todo_id)
            # raise AuthorizationException("You are not authorized to delete this ToDo.")

        # BaseRepository の delete メソッドを使用 (ID指定で削除)
        deleted = await self.repository.delete(id=todo_id)
        # delete メソッドが None を返す可能性があるため、確認は db_todo で行う
        if deleted:
             logger.info("Service: Todo deleted successfully", todo_id=todo_id, owner_id=owner_id)
             # TODO: イベント発行 (例: todo_deleted)
        else:
             # これは通常発生しないはず (上で存在確認しているため)
             logger.error("Service: Failed to delete todo after existence check", todo_id=todo_id, owner_id=owner_id)
             raise ResourceNotFoundException(resource_name="ToDo", resource_id=todo_id) # or Internal Server Error?

        # 削除成功時は何も返さない (API層で 204 No Content を返す想定)
        return None

