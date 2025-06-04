# src/db/session.py
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text  # connect_dbで使用するためここで先にインポート
from fastapi import HTTPException

from libkoiki.core.config import settings
from libkoiki.core.logging import get_logger

logger = get_logger(__name__)

# グローバル変数
engine: AsyncEngine = None
async_session_factory = None

# AsyncSessionFactory の名前で async_session_factory をエクスポート
AsyncSessionFactory = None

def init_db_engine():
    """非同期SQLAlchemyエンジンとセッションファクトリを初期化"""
    global engine
    global async_session_factory
    global AsyncSessionFactory  # 追加
    
    try:
        db_url = settings.DATABASE_URL
        
        # PostgreSQL接続初期化
        connect_args = {}
        logger.info("Initializing PostgreSQL database engine.", 
                    db_url=f"postgresql+asyncpg://...@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        
        # エンジンの初期化
        engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            connect_args=connect_args,
            poolclass=NullPool if settings.APP_ENV == "testing" else None,
        )
        
        # セッションファクトリの初期化
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # AsyncSessionFactory を async_session_factory と同じものに設定
        AsyncSessionFactory = async_session_factory
        
        logger.info("Database engine and session factory initialized successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}", exc_info=True)
        raise RuntimeError(f"Database engine initialization failed: {e}")

async def dispose_db_engine():
    """データベースエンジンを破棄"""
    global engine
    if engine:
        logger.info("Disposing database engine.")
        await engine.dispose()
        engine = None
        logger.info("Database engine disposed.")

# --- 依存性注入用 非同期セッションジェネレータ ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    リクエストスコープのDBセッションを提供する非同期ジェネレータ。
    FastAPI の Depends() で使用される。
    """
    if AsyncSessionFactory is None:
        logger.critical("Database session factory is not initialized. Call init_db_engine() first.")
        raise RuntimeError("Database session factory is not initialized.")

    # logger.debug("Creating new database session for request.")
    async with AsyncSessionFactory() as session:
        # logger.debug(f"DB Session {id(session)} obtained from factory.")
        try:
            yield session
            # トランザクション管理は @transactional デコレータに任せる
            # もしデコレータを使わない読み取り操作などで必要なら、ここで commit/rollback する
            # try:
            #     await session.commit()
            # except SQLAlchemyError:
            #     await session.rollback()
            #     raise
        except SQLAlchemyError as db_exc: # データベース操作中の例外
            logger.error(f"Database error occurred in session {id(session)}, rolling back.", exc_info=False, error=str(db_exc))
            try:
                await session.rollback()
                logger.info(f"Session {id(session)} rolled back due to SQLAlchemyError.")
            except Exception as rollback_exc:
                 logger.error(f"Error during rollback for session {id(session)}", exc_info=True, original_error=str(db_exc))
            raise # 元のDBエラーを再送出 -> グローバルハンドラで処理
        except HTTPException:
             # FastAPI の HTTPException (例: 404 Not Found) はそのまま送出
             # logger.debug(f"HTTPException caught in session {id(session)}, rolling back.")
             await session.rollback() # HTTPエラーでもDB操作はロールバックすべき
             raise
        except Exception as e: # その他の予期せぬ例外
            logger.error(f"Unexpected error in session {id(session)}, rolling back.", exc_info=True)
            try:
                await session.rollback()
                logger.warning(f"Session {id(session)} rolled back due to unexpected error.")
            except Exception as rollback_exc:
                 logger.error(f"Error during rollback after unexpected error in session {id(session)}", exc_info=True, original_error=str(e))
            raise # 元の例外を再送出 -> グローバルハンドラで処理
        finally:
            # セッションは `async with AsyncSessionFactory() as session:` で自動的に閉じられる
            # logger.debug(f"DB Session {id(session)} closed.")
            pass


# --- アプリケーション起動/終了時のヘルパー関数 ---
async def connect_db():
    """アプリケーション起動時のDB接続確認"""
    init_db_engine() # エンジンとファクトリを初期化
    if engine:
        try:
            async with engine.connect() as conn:
                # 簡単なクエリを実行して接続を確認
                await conn.execute(text("SELECT 1"))
                logger.info("Database connection successful.")
                logger.info("PostgreSQL database connection verified.")
        except Exception as e:
            logger.error(f"Database connection failed: {e}", exc_info=True)
            # 接続失敗時の処理 (リトライ or 終了)
            raise RuntimeError(f"Database connection failed: {e}")
    else:
        logger.error("Database engine is not initialized after init_db_engine call.")
        raise RuntimeError("Database engine initialization failed silently.")


async def disconnect_db():
    """アプリケーション終了時のDBエンジン破棄"""
    await dispose_db_engine()
