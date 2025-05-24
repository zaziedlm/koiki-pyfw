# src/repositories/base.py
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Sequence, Union # Union をインポート
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sql_delete, update as sql_update # updateもインポート
from sqlalchemy.orm import sessionmaker # Sessionタイプヒント用に必要なら
from pydantic import BaseModel
import structlog

from libkoiki.db.base import Base # ORM Base

logger = structlog.get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base) # SQLAlchemyモデル
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel) # Pydantic作成スキーマ
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel) # Pydantic更新スキーマ

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    基本的なCRUD操作を提供するジェネリックなベースリポジトリ。
    非同期 SQLAlchemy セッションを使用します。
    """
    model: Type[ModelType] # 型ヒントを追加

    def __init__(self, model: Type[ModelType]):
        """
        コンストラクタ。操作対象の SQLAlchemy モデルクラスを受け取ります。
        セッションはメソッド呼び出し時に `set_session` で設定されることを想定します。
        """
        self.model = model
        self._db: Optional[AsyncSession] = None # 遅延設定されるセッション

    def set_session(self, db: AsyncSession):
        """現在のリクエスト/トランザクションのDBセッションを設定します"""
        # logger.debug(f"Setting session {id(db)} for repository {self.__class__.__name__}")
        self._db = db

    @property
    def db(self) -> AsyncSession:
        """
        現在のDBセッションを取得します。セッションが設定されていない場合は例外を送出します。
        """
        if self._db is None:
            # トランザクションデコレータやサービス層で事前に set_session が呼ばれることを期待
            logger.error(f"Database session not set for repository {self.__class__.__name__}")
            # ここで例外を発生させることで、セッション設定漏れに気づきやすくなる
            raise Exception(f"Database session not set for repository {self.__class__.__name__}")
        return self._db

    async def get(self, id: Any) -> Optional[ModelType]:
        """IDに基づいて単一のオブジェクトを取得します"""
        logger.debug(f"Getting {self.model.__name__} by id", id=id)
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        instance = result.scalar_one_or_none()
        # if instance is None:
        #     logger.debug(f"{self.model.__name__} not found by id", id=id)
        return instance

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """
        複数オブジェクトをページネーション付きで取得します。
        デフォルトではID順にソートされます。
        """
        logger.debug(f"Getting multiple {self.model.__name__}", skip=skip, limit=limit)
        stmt = select(self.model).offset(skip).limit(limit).order_by(self.model.id) # デフォルトの順序付け
        result = await self.db.execute(stmt)
        instances = result.scalars().all()
        # logger.debug(f"Found {len(instances)} instances of {self.model.__name__}")
        return instances

    async def create(self, obj_in: ModelType) -> ModelType:
        """
        新しいオブジェクトを作成します。ORMモデルインスタンスを受け取ります。
        サービス層でインスタンス化され、データが設定されていることを想定します。
        コミットはトランザクション管理デコレータが行います。
        """
        logger.debug(f"Creating new {self.model.__name__}", data=obj_in.__dict__) # データ内容をログ出力（注意）
        self.db.add(obj_in)
        try:
            await self.db.flush() # DBに即時反映させてIDなどを確定させる
            await self.db.refresh(obj_in) # DBから最新の状態 (ID, server_default値など) を読み込む
            logger.info(f"{self.model.__name__} created successfully", id=obj_in.id)
            return obj_in
        except Exception as e:
            logger.error(f"Error during flush/refresh after creating {self.model.__name__}", exc_info=True)
            # ここでロールバックはしない（トランザクションデコレータに任せる）
            raise # 例外を再送出

    async def update(
        self, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        既存のオブジェクトを更新します。
        ORMモデルインスタンスと、更新データ (Pydanticスキーマまたは辞書) を受け取ります。
        コミットはトランザクション管理デコレータが行います。
        """
        logger.debug(f"Updating {self.model.__name__}", id=db_obj.id, update_data=obj_in)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # exclude_unset=True で Pydantic スキーマで未指定のフィールドを無視
            update_data = obj_in.dict(exclude_unset=True)

        if not update_data:
             logger.warning(f"Update called for {self.model.__name__} with no data to update", id=db_obj.id)
             return db_obj # 更新データがなければ何もしない

        # モデルのフィールドを更新
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
            else:
                logger.warning(f"Attempted to update non-existent field '{field}' for {self.model.__name__}", id=db_obj.id)


        self.db.add(db_obj) # セッションに変更をマーク (既存オブジェクトの場合 add は必須ではないが害はない)
        try:
            await self.db.flush() # DBに変更を反映
            await self.db.refresh(db_obj) # DBから最新の状態を読み込む
            logger.info(f"{self.model.__name__} updated successfully", id=db_obj.id)
            return db_obj
        except Exception as e:
            logger.error(f"Error during flush/refresh after updating {self.model.__name__}", id=db_obj.id, exc_info=True)
            raise

    async def delete(self, id: Any) -> Optional[ModelType]:
        """
        IDに基づいてオブジェクトを削除します。
        コミットはトランザクション管理デコレータが行います。
        """
        logger.debug(f"Deleting {self.model.__name__} by id", id=id)
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush() # DBに変更を反映
            logger.info(f"{self.model.__name__} deleted successfully", id=id)
            return obj # 削除されたオブジェクトを返す (Noneの場合もある)
        else:
            logger.warning(f"Attempted to delete non-existent {self.model.__name__}", id=id)
            return None

    # --- その他の便利なメソッド (オプション) ---

    async def get_or_none(self, id: Any) -> Optional[ModelType]:
        """`get` と同じですが、見つからない場合に警告ログを出しません"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """テーブルの総件数を取得します"""
        # count(*) は低速になる可能性があるため注意
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return result.scalar_one()
