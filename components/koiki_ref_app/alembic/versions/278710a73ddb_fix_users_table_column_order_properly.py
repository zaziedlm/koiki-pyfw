"""fix_users_table_column_order_properly

Revision ID: 278710a73ddb
Revises: f1e6d6de66b7
Create Date: 2025-07-12 20:43:28.885749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '278710a73ddb'
down_revision: Union[str, None] = 'f1e6d6de66b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # usersテーブルのカラム順序を正しい順序に修正
    # 現在: username, id, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
    # 理想: id, username, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
    
    # 1. 正しいカラム順序で新しいテーブルを作成
    op.execute("""
        CREATE TABLE users_proper (
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
    
    # 2. 既存データを正しい順序でコピー
    op.execute("""
        INSERT INTO users_proper (id, username, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at)
        SELECT id, username, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
        FROM users
        ORDER BY id
    """)
    
    # 3. usersテーブルを参照する全外部キー制約を動的に削除
    op.execute("""
        DO $$
        DECLARE constraint_record RECORD;
        BEGIN
            FOR constraint_record IN
                SELECT conname, n.nspname, c.relname
                FROM pg_constraint AS con
                JOIN pg_class AS c ON con.conrelid = c.oid
                JOIN pg_namespace AS n ON c.relnamespace = n.oid
                WHERE con.contype = 'f'
                  AND con.confrelid = 'users'::regclass
            LOOP
                EXECUTE format(
                    'ALTER TABLE %I.%I DROP CONSTRAINT %I',
                    constraint_record.nspname,
                    constraint_record.relname,
                    constraint_record.conname
                );
            END LOOP;
        END $$;
    """)
    
    # 4. 元のテーブルを削除
    op.drop_table('users')
    
    # 5. 新しいテーブルをusersにリネーム
    op.execute('ALTER TABLE users_proper RENAME TO users')
    
    # 6. シーケンスの調整
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_proper_id_seq') THEN
                PERFORM setval('users_proper_id_seq', (SELECT MAX(id) FROM users));
                ALTER SEQUENCE users_proper_id_seq RENAME TO users_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_id_seq') THEN
                PERFORM setval('users_id_seq', (SELECT MAX(id) FROM users));
            END IF;
        END $$;
    """)
    
    # 7. インデックスを再作成
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_full_name', 'users', ['full_name'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('login_attempts_user_id_fkey', 'login_attempts', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('refresh_tokens_user_id_fkey', 'refresh_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('todos_owner_id_fkey', 'todos', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_sso_user_id_fkey', 'user_sso', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # ダウングレード: 元の順序に戻す（username, id, email, ...）
    
    # 1. 元の順序でテーブルを作成
    op.execute("""
        CREATE TABLE users_old (
            username VARCHAR(50) NOT NULL UNIQUE,
            id SERIAL PRIMARY KEY,
            email VARCHAR UNIQUE,
            full_name VARCHAR,
            hashed_password VARCHAR,
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    
    # 2. データをコピー
    op.execute("""
        INSERT INTO users_old (username, id, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at)
        SELECT username, id, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
        FROM users
        ORDER BY id
    """)
    
    # 3. usersテーブルを参照する外部キー制約を動的に削除
    op.execute("""
        DO $$
        DECLARE constraint_record RECORD;
        BEGIN
            FOR constraint_record IN
                SELECT conname, n.nspname, c.relname
                FROM pg_constraint AS con
                JOIN pg_class AS c ON con.conrelid = c.oid
                JOIN pg_namespace AS n ON c.relnamespace = n.oid
                WHERE con.contype = 'f'
                  AND con.confrelid = 'users'::regclass
            LOOP
                EXECUTE format(
                    'ALTER TABLE %I.%I DROP CONSTRAINT %I',
                    constraint_record.nspname,
                    constraint_record.relname,
                    constraint_record.conname
                );
            END LOOP;
        END $$;
    """)
    
    # 4. 現在のテーブルを削除
    op.drop_table('users')
    
    # 5. 元のテーブルをusersにリネーム
    op.execute('ALTER TABLE users_old RENAME TO users')
    
    # 6. シーケンスの調整
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_old_id_seq') THEN
                PERFORM setval('users_old_id_seq', (SELECT MAX(id) FROM users));
                ALTER SEQUENCE users_old_id_seq RENAME TO users_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'users_id_seq') THEN
                PERFORM setval('users_id_seq', (SELECT MAX(id) FROM users));
            END IF;
        END $$;
    """)
    
    # 7. インデックスを再作成
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_full_name', 'users', ['full_name'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('login_attempts_user_id_fkey', 'login_attempts', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('refresh_tokens_user_id_fkey', 'refresh_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('todos_owner_id_fkey', 'todos', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_sso_user_id_fkey', 'user_sso', 'users', ['user_id'], ['id'], ondelete='CASCADE')
