# alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

ALEMBIC_DIR = os.path.dirname(__file__)
COMPONENT_ROOT = os.path.realpath(os.path.join(ALEMBIC_DIR, ".."))
REPO_ROOT = os.path.realpath(os.path.join(COMPONENT_ROOT, "..", ".."))
KOIKI_REF_APP_SRC = os.path.join(COMPONENT_ROOT, "src")
LIBKOIKI_SRC = os.path.join(REPO_ROOT, "components", "libkoiki", "src")

for path in (KOIKI_REF_APP_SRC, LIBKOIKI_SRC, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- ORM bootstrap ---
from koiki_ref_app.bootstrap import bootstrap_orm
from koiki_ref_app.db.base import Base as AppBase
bootstrap_orm()
from libkoiki.core.config import settings  # アプリケーション設定を読み込む

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- データベース接続設定 ---
# alembic.ini の sqlalchemy.url をアプリケーション設定から取得した同期URLで上書き
# Alembic はマイグレーション生成・適用時に同期接続を使用するため
if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not configured. Run Alembic with "
        "`uv run --locked alembic -c components/koiki_ref_app/alembic.ini ...` "
        "and set DATABASE_URL. Use host `localhost` from the local machine and "
        "host `db` from inside Docker Compose containers."
    )

# PostgreSQL用に同期DB URLに変換
# asyncpg -> psycopg2 に変換
sync_db_url = str(settings.DATABASE_URL).replace("+asyncpg", "")

config.set_main_option("sqlalchemy.url", sync_db_url)

# --- ターゲットメタデータの設定 ---
# Autogenerateのためにモデルのメタデータを設定
target_metadata = AppBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:  # async を削除
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # iniファイルから設定を読み込む
    connectable_config = config.get_section(config.config_ini_section)
    # 設定から同期URLを取得 (非同期マイグレーションではなく、接続確認に使用)
    connectable_config["sqlalchemy.url"] = sync_db_url

    # 同期エンジンを使用する
    connectable = engine_from_config(
        connectable_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # future=True # SQLAlchemy 2.0 スタイル
    )

    with connectable.connect() as connection:  # async を削除
        do_run_migrations(connection)  # await connection.run_sync を変更

    # 同期エンジンの場合、disposeは通常不要 (特にNullPoolの場合)
    # connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # import asyncio # asyncioを削除
    run_migrations_online()  # asyncio.runを削除
