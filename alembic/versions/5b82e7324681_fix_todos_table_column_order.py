# alembic/script.py.mako
"""fix_todos_table_column_order

Revision ID: 5b82e7324681
Revises: '278710a73ddb'
Create Date: 2025-07-12 20:53:06.039743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b82e7324681'
down_revision: Union[str, None] = '278710a73ddb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # todosテーブルのカラム順序を理想的な順序に修正
    # 現在: title, description, is_completed, owner_id, id, created_at, updated_at
    # 理想: id, title, owner_id, description, is_completed, created_at, updated_at
    
    # 1. 理想的なカラム順序で新しいテーブルを作成
    op.execute("""
        CREATE TABLE todos_proper (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            owner_id INTEGER NOT NULL,
            description TEXT,
            is_completed BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    
    # 2. 既存データを新しいテーブルにコピー（データが存在する場合）
    op.execute("""
        INSERT INTO todos_proper (id, title, owner_id, description, is_completed, created_at, updated_at)
        SELECT id, title, owner_id, description, is_completed, created_at, updated_at
        FROM todos
        ORDER BY id
    """)
    
    # 3. 元のテーブルを削除
    op.drop_table('todos')
    
    # 4. 新しいテーブルをtodosにリネーム
    op.execute('ALTER TABLE todos_proper RENAME TO todos')
    
    # 5. シーケンスの調整
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'todos_proper_id_seq') THEN
                PERFORM setval('todos_proper_id_seq', COALESCE((SELECT MAX(id) FROM todos), 1));
                ALTER SEQUENCE todos_proper_id_seq RENAME TO todos_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'todos_id_seq') THEN
                PERFORM setval('todos_id_seq', COALESCE((SELECT MAX(id) FROM todos), 1));
            END IF;
        END $$;
    """)
    
    # 6. インデックスを再作成
    op.create_index('ix_todos_id', 'todos', ['id'])
    op.create_index('ix_todos_title', 'todos', ['title'])
    op.create_index('ix_todos_owner_id', 'todos', ['owner_id'])
    
    # 7. 外部キー制約を再作成
    op.create_foreign_key('todos_owner_id_fkey', 'todos', 'users', ['owner_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # ダウングレード: 元の順序に戻す
    # 元の順序: title, description, is_completed, owner_id, id, created_at, updated_at
    
    # 1. 元の順序でテーブルを作成
    op.execute("""
        CREATE TABLE todos_old (
            title VARCHAR(255) NOT NULL,
            description TEXT,
            is_completed BOOLEAN NOT NULL DEFAULT false,
            owner_id INTEGER NOT NULL,
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    
    # 2. データをコピー
    op.execute("""
        INSERT INTO todos_old (title, description, is_completed, owner_id, id, created_at, updated_at)
        SELECT title, description, is_completed, owner_id, id, created_at, updated_at
        FROM todos
        ORDER BY id
    """)
    
    # 3. 外部キー制約を削除
    op.drop_constraint('todos_owner_id_fkey', 'todos', type_='foreignkey')
    
    # 4. 現在のテーブルを削除
    op.drop_table('todos')
    
    # 5. 元のテーブルをtodosにリネーム
    op.execute('ALTER TABLE todos_old RENAME TO todos')
    
    # 6. シーケンスの調整
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'todos_old_id_seq') THEN
                PERFORM setval('todos_old_id_seq', COALESCE((SELECT MAX(id) FROM todos), 1));
                ALTER SEQUENCE todos_old_id_seq RENAME TO todos_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'todos_id_seq') THEN
                PERFORM setval('todos_id_seq', COALESCE((SELECT MAX(id) FROM todos), 1));
            END IF;
        END $$;
    """)
    
    # 7. インデックスを再作成
    op.create_index('ix_todos_id', 'todos', ['id'])
    op.create_index('ix_todos_title', 'todos', ['title'])
    op.create_index('ix_todos_owner_id', 'todos', ['owner_id'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('todos_owner_id_fkey', 'todos', 'users', ['owner_id'], ['id'], ondelete='CASCADE')