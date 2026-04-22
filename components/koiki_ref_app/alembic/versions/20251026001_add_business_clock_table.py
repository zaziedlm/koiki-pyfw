"""Add business_clock table for business time control.

Revision ID: 20251026001
Revises: 20251010001
Create Date: 2025-10-26 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251026001"
down_revision = "20251010002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_clock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default="REALTIME"),
        sa.Column("base_timezone", sa.String(length=64), nullable=False, server_default="Asia/Tokyo"),
        sa.Column("frozen_business_date", sa.Date(), nullable=True),
        sa.Column("frozen_business_time", sa.Time(), nullable=True),
        sa.Column("offset_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("offset_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_by", sa.String(length=255), nullable=False, server_default="system"),
        sa.CheckConstraint("id = 1", name="ck_business_clock_singleton"),
    )

    op.execute(
        """
        INSERT INTO business_clock (id, mode, base_timezone, offset_days, offset_minutes, version, updated_by)
        VALUES (1, 'REALTIME', 'Asia/Tokyo', 0, 0, 1, 'system')
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_table("business_clock")
