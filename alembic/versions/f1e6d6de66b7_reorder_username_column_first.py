# alembic/script.py.mako
"""reorder_users_table_columns_properly

Revision ID: f1e6d6de66b7
Revises: 'f4898f31a506'
Create Date: 2025-07-12 20:37:53.624932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1e6d6de66b7'
down_revision: Union[str, None] = 'f4898f31a506'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # usersテーブルのカラム順序を理想的な順序に修正
    # 理想順序: id, username, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
    
    # 1. 理想的なカラム順序で新しいテーブルを作成
    op.execute("""
        CREATE TABLE users_new (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR UNIQUE,
            full_name VARCHAR,
            hashed_password VARCHAR,
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    
    # 2. 既存データを新しいテーブルにコピー（理想的なカラム順序で）
    op.execute("""
        INSERT INTO users_new (id, username, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at)
        SELECT id, username, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
        FROM users
        ORDER BY id
    """)
    
    # 3. 外部キー制約を一時的に削除
    op.drop_constraint('login_attempts_user_id_fkey', 'login_attempts', type_='foreignkey')
    op.drop_constraint('password_reset_tokens_user_id_fkey', 'password_reset_tokens', type_='foreignkey')
    op.drop_constraint('refresh_tokens_user_id_fkey', 'refresh_tokens', type_='foreignkey')
    op.drop_constraint('todos_owner_id_fkey', 'todos', type_='foreignkey')
    op.drop_constraint('user_roles_user_id_fkey', 'user_roles', type_='foreignkey')
    
    # 4. 元のテーブルを削除
    op.drop_table('users')
    
    # 5. 新しいテーブルをusersにリネーム
    op.execute('ALTER TABLE users_new RENAME TO users')
    
    # 6. シーケンスの値を調整（新しいシーケンスが作成されているかチェック）
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_new_id_seq') THEN
                PERFORM setval('users_new_id_seq', (SELECT MAX(id) FROM users));
                ALTER SEQUENCE users_new_id_seq RENAME TO users_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_id_seq') THEN
                PERFORM setval('users_id_seq', (SELECT MAX(id) FROM users));
            END IF;
        END $$;
    """)
    
    # 7. インデックスを再作成
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_full_name', 'users', ['full_name'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('login_attempts_user_id_fkey', 'login_attempts', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('refresh_tokens_user_id_fkey', 'refresh_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('todos_owner_id_fkey', 'todos', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # ダウングレード: 元の順序に戻す
    
    # 1. 元の順序でテーブルを作成
    op.execute("""
        CREATE TABLE users_old (
            id SERIAL PRIMARY KEY,
            email VARCHAR UNIQUE,
            hashed_password VARCHAR,
            full_name VARCHAR,
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            username VARCHAR(50) NOT NULL UNIQUE
        )
    """)
    
    # 2. データをコピー
    op.execute("""
        INSERT INTO users_old (id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at, username)
        SELECT id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at, username
        FROM users
        ORDER BY id
    """)
    
    # 3. 外部キー制約を削除
    op.drop_constraint('login_attempts_user_id_fkey', 'login_attempts', type_='foreignkey')
    op.drop_constraint('password_reset_tokens_user_id_fkey', 'password_reset_tokens', type_='foreignkey')
    op.drop_constraint('refresh_tokens_user_id_fkey', 'refresh_tokens', type_='foreignkey')
    op.drop_constraint('todos_owner_id_fkey', 'todos', type_='foreignkey')
    op.drop_constraint('user_roles_user_id_fkey', 'user_roles', type_='foreignkey')
    
    # 4. 現在のテーブルを削除
    op.drop_table('users')
    
    # 5. 元のテーブルをusersにリネーム
    op.execute('ALTER TABLE users_old RENAME TO users')
    
    # 6. シーケンスの値を調整
    op.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
    
    # 7. インデックスを再作成
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_full_name', 'users', ['full_name'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('login_attempts_user_id_fkey', 'login_attempts', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('refresh_tokens_user_id_fkey', 'refresh_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('todos_owner_id_fkey', 'todos', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])