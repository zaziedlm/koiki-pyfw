"""Rename business_clock table to kkbiz_business_clock.

Revision ID: 20251030001
Revises: 20251026001
Create Date: 2025-10-30 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251030001"
down_revision = "20251026001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("business_clock", "kkbiz_business_clock")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_name = 'ck_business_clock_singleton'
                  AND table_schema = current_schema()
            ) THEN
                EXECUTE 'ALTER TABLE kkbiz_business_clock RENAME CONSTRAINT ck_business_clock_singleton TO ck_kkbiz_business_clock_singleton';
            END IF;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_name = 'ck_kkbiz_business_clock_singleton'
                  AND table_schema = current_schema()
            ) THEN
                EXECUTE 'ALTER TABLE kkbiz_business_clock RENAME CONSTRAINT ck_kkbiz_business_clock_singleton TO ck_business_clock_singleton';
            END IF;
        END;
        $$;
        """
    )

    op.rename_table("kkbiz_business_clock", "business_clock")
