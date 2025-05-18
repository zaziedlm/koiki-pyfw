# src/core/transaction.py
import functools
from typing import Callable, Any, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import Depends # Depends はここでは使わない
import structlog

# from libkoiki.db.session import get_db as get_db_session # get_db はエンドポイント層の依存性として使う
# from libkoiki.core.exceptions import BaseAppException # 必要ならインポート

logger = structlog.get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def transactional(func: F) -> F:
    """
    サービスメソッドをデータベーストランザクション内で実行するデコレータ。
    メソッドは最後の引数として AsyncSession を受け取る必要がある。
    メソッド内でリポジトリ等にセッションを渡す必要がある。
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 呼び出し元の引数から AsyncSession を探す
        # 通常、サービスメソッドの最後の引数として渡されることを期待
        db_session: Optional[AsyncSession] = None
        session_arg_index = -1

        # 位置引数の最後が AsyncSession かチェック
        if args and isinstance(args[-1], AsyncSession):
            db_session = args[-1]
            session_arg_index = len(args) - 1
        # キーワード引数に AsyncSession があるかチェック (例: db=session)
        elif 'db' in kwargs and isinstance(kwargs['db'], AsyncSession):
            db_session = kwargs['db']
        # 他のキーワード引数名も探す場合 (より汎用的だが複雑)
        # else:
        #     for k, v in kwargs.items():
        #         if isinstance(v, AsyncSession):
        #             db_session = v
        #             break

        if db_session is None:
            logger.error("Transactional decorator requires an AsyncSession argument in the decorated function", function_name=func.__name__)
            raise TypeError(f"Function '{func.__name__}' decorated with @transactional must accept an AsyncSession as an argument (e.g., 'db: AsyncSession').")

        # サービスインスタンス (self) を取得 (メソッドの場合)
        # self = args[0] if args and hasattr(args[0], func.__name__) else None

        try:
            # トランザクションが既に開始されているかチェック (ネストトランザクション非対応の簡易版)
            if db_session.in_transaction():
                 logger.debug("Transaction already active, participating", function_name=func.__name__)
                 # ネストトランザクションをサポートする場合は `db_session.begin_nested()` を使う
            else:
                 logger.debug("Starting new transaction", function_name=func.__name__)
                 # begin() は AsyncSession コンテキストマネージャー内で自動的に呼ばれることが多いが、
                 # 明示的に開始することもできる（セッションの状態による）
                 # await db_session.begin() # 不要な場合が多い

            # --- サービスメソッド内でリポジトリにセッションを設定 ---
            # デコレータが引数からサービスインスタンスを取得し、
            # そのリポジトリにセッションを設定する方式も考えられるが、
            # サービスメソッド内で明示的に `repo.set_session(db)` する方が確実。
            # if self and hasattr(self, 'repository') and hasattr(self.repository, 'set_session'):
            #     self.repository.set_session(db_session)
            # elif self and hasattr(self, 'repositories'): # 複数のリポジトリを持つ場合
            #     for repo in self.repositories:
            #         if hasattr(repo, 'set_session'):
            #             repo.set_session(db_session)

            # --- メソッド実行 ---
            # デコレータが付加された元の関数を実行
            # db セッションは引数として渡されているので、そのまま実行
            result = await func(*args, **kwargs)

            # --- コミット ---
            # トランザクションがネストされている場合、トップレベルのトランザクションでのみコミット
            if db_session.in_transaction(): # まだトランザクション中か確認
                 try:
                     await db_session.commit()
                     logger.debug("Transaction committed", function_name=func.__name__)
                 except Exception as commit_exc:
                     logger.error("Error during transaction commit, attempting rollback", function_name=func.__name__, exc_info=True)
                     await db_session.rollback()
                     logger.warning("Transaction rolled back after commit error", function_name=func.__name__)
                     raise commit_exc # コミットエラーも再送出

            return result

        except Exception as e:
            # --- ロールバック ---
            logger.error("Exception occurred within transaction, rolling back", function_name=func.__name__, error=str(e), exc_info=True)
            if db_session.in_transaction(): # トランザクション中ならロールバック
                try:
                    await db_session.rollback()
                    logger.info("Transaction rolled back successfully", function_name=func.__name__)
                except Exception as rollback_exc:
                    # ロールバック自体に失敗した場合 (深刻な状況)
                    logger.critical("Failed to rollback transaction!", function_name=func.__name__, rollback_error=str(rollback_exc), original_error=str(e), exc_info=True)
            # 元の例外を再送出
            raise e
        # finally ブロックは不要 (セッションのクローズは get_db 依存性で行う)

    return wrapper # type: ignore

# 使用例:
# from sqlalchemy.ext.asyncio import AsyncSession
# from libkoiki.repositories.base import BaseRepository
#
# class MyService:
#     def __init__(self, repo: BaseRepository):
#         self.repository = repo
#
#     @transactional
#     async def create_something(self, data: dict, db: AsyncSession):
#         # ★重要: サービスメソッド内でリポジトリにセッションを渡す★
#         self.repository.set_session(db)
#
#         item = await self.repository.create(Model(**data))
#         # ... 他のDB操作 ...
#         return item
