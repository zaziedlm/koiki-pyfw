"""Add application-specific columns to user_sso

Revision ID: 20251010001
Revises: 38e7ad6278bf
Create Date: 2025-10-10 23:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251010001"
down_revision = "38e7ad6278bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add app_id/app_created_at/app_updated_at columns to user_sso."""
    op.add_column(
        "user_sso",
        sa.Column("app_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_sso",
        sa.Column(
            "app_created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "user_sso",
        sa.Column(
            "app_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Align new timestamp columns with existing historical data.
    op.execute(
        """
        UPDATE user_sso
        SET
            app_created_at = created_at,
            app_updated_at = updated_at
        """
    )

    # Prepare a sequence for application-specific identifiers.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_class
                WHERE relkind = 'S' AND relname = 'user_sso_app_id_seq'
            ) THEN
                CREATE SEQUENCE user_sso_app_id_seq OWNED BY user_sso.app_id;
            END IF;
        END
        $$;
        """
    )

    # Populate existing rows and sync the sequence.
    op.execute("UPDATE user_sso SET app_id = id WHERE app_id IS NULL;")
    op.execute(
        """
        DO $$
        DECLARE
            max_val INTEGER;
        BEGIN
            SELECT MAX(app_id) INTO max_val FROM user_sso;
            IF max_val IS NULL THEN
                PERFORM setval('user_sso_app_id_seq', 1, false);
            ELSE
                PERFORM setval('user_sso_app_id_seq', max_val, true);
            END IF;
        END
        $$;
        """
    )

    # Enforce defaults and constraints for future records.
    op.alter_column(
        "user_sso",
        "app_id",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text("nextval('user_sso_app_id_seq')"),
    )
    op.create_unique_constraint(
        "uq_user_sso_app_id",
        "user_sso",
        ["app_id"],
    )
    op.create_index(
        "ix_user_sso_app_id",
        "user_sso",
        ["app_id"],
    )


def downgrade() -> None:
    """Remove application-specific columns and related database objects."""
    op.drop_index("ix_user_sso_app_id", table_name="user_sso")
    op.drop_constraint("uq_user_sso_app_id", "user_sso", type_="unique")
    op.alter_column(
        "user_sso",
        "app_id",
        existing_type=sa.Integer(),
        server_default=None,
    )
    op.drop_column("user_sso", "app_updated_at")
    op.drop_column("user_sso", "app_created_at")
    op.drop_column("user_sso", "app_id")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_class
                WHERE relkind = 'S' AND relname = 'user_sso_app_id_seq'
            ) THEN
                DROP SEQUENCE user_sso_app_id_seq;
            END IF;
        END
        $$;
        """
    )
