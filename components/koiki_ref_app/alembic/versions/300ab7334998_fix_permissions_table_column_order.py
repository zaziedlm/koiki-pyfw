# alembic/script.py.mako
"""fix_permissions_table_column_order

Revision ID: 300ab7334998
Revises: '5b82e7324681'
Create Date: 2025-07-12 20:56:09.412925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '300ab7334998'
down_revision: Union[str, None] = '5b82e7324681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # permissionsテーブルのカラム順序を理想的な順序に修正
    # 現在: name, description, id, created_at, updated_at, resource, action
    # 理想: id, name, resource, action, description, created_at, updated_at
    
    # 1. 理想的なカラム順序で新しいテーブルを作成
    op.execute("""
        CREATE TABLE permissions_proper (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            resource VARCHAR(50),
            action VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    
    # 2. 既存データを新しいテーブルにコピー
    op.execute("""
        INSERT INTO permissions_proper (id, name, resource, action, description, created_at, updated_at)
        SELECT id, name, resource, action, description, created_at, updated_at
        FROM permissions
        ORDER BY id
    """)
    
    # 3. 外部キー制約を一時的に削除
    op.drop_constraint('role_permissions_permission_id_fkey', 'role_permissions', type_='foreignkey')
    
    # 4. 元のテーブルを削除
    op.drop_table('permissions')
    
    # 5. 新しいテーブルをpermissionsにリネーム
    op.execute('ALTER TABLE permissions_proper RENAME TO permissions')
    
    # 6. シーケンスの調整
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'permissions_proper_id_seq') THEN
                PERFORM setval('permissions_proper_id_seq', (SELECT MAX(id) FROM permissions));
                ALTER SEQUENCE permissions_proper_id_seq RENAME TO permissions_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'permissions_id_seq') THEN
                PERFORM setval('permissions_id_seq', (SELECT MAX(id) FROM permissions));
            END IF;
        END $$;
    """)
    
    # 7. インデックスを再作成
    op.create_index('ix_permissions_id', 'permissions', ['id'])
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=True)
    op.create_index('ix_permissions_resource', 'permissions', ['resource'])
    op.create_index('ix_permissions_action', 'permissions', ['action'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('role_permissions_permission_id_fkey', 'role_permissions', 'permissions', ['permission_id'], ['id'])


def downgrade() -> None:
    # ダウングレード: 元の順序に戻す
    # 元の順序: name, description, id, created_at, updated_at, resource, action
    
    # 1. 元の順序でテーブルを作成
    op.execute("""
        CREATE TABLE permissions_old (
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            resource VARCHAR(50),
            action VARCHAR(50)
        )
    """)
    
    # 2. データをコピー
    op.execute("""
        INSERT INTO permissions_old (name, description, id, created_at, updated_at, resource, action)
        SELECT name, description, id, created_at, updated_at, resource, action
        FROM permissions
        ORDER BY id
    """)
    
    # 3. 外部キー制約を削除
    op.drop_constraint('role_permissions_permission_id_fkey', 'role_permissions', type_='foreignkey')
    
    # 4. 現在のテーブルを削除
    op.drop_table('permissions')
    
    # 5. 元のテーブルをpermissionsにリネーム
    op.execute('ALTER TABLE permissions_old RENAME TO permissions')
    
    # 6. シーケンスの調整
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'permissions_old_id_seq') THEN
                PERFORM setval('permissions_old_id_seq', (SELECT MAX(id) FROM permissions));
                ALTER SEQUENCE permissions_old_id_seq RENAME TO permissions_id_seq;
            ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'permissions_id_seq') THEN
                PERFORM setval('permissions_id_seq', (SELECT MAX(id) FROM permissions));
            END IF;
        END $$;
    """)
    
    # 7. インデックスを再作成
    op.create_index('ix_permissions_id', 'permissions', ['id'])
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=True)
    op.create_index('ix_permissions_resource', 'permissions', ['resource'])
    op.create_index('ix_permissions_action', 'permissions', ['action'])
    
    # 8. 外部キー制約を再作成
    op.create_foreign_key('role_permissions_permission_id_fkey', 'role_permissions', 'permissions', ['permission_id'], ['id'])