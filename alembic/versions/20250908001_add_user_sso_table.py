"""Add UserSSO table for SSO authentication

Revision ID: 20250908001
Revises: f1e6d6de66b7
Create Date: 2025-09-08 15:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250908001"
down_revision = "f1e6d6de66b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add user_sso table for SSO authentication support

    This table manages the linkage between local users and external SSO providers,
    allowing users to authenticate through OpenID Connect and other SSO services.
    """
    op.create_table(
        "user_sso",
        # Primary key
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        # Foreign key to users table
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="連携するローカルユーザーID",
        ),
        # SSO provider identification
        sa.Column(
            "sso_subject_id",
            sa.String(255),
            nullable=False,
            comment="SSOサービスでの一意識別子 (sub claim)",
        ),
        sa.Column(
            "sso_provider",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'oidc'"),
            comment="SSOプロバイダー識別子",
        ),
        # SSO metadata
        sa.Column(
            "sso_email",
            sa.String(255),
            nullable=True,
            comment="SSO側で管理されているメールアドレス",
        ),
        sa.Column(
            "sso_display_name",
            sa.String(100),
            nullable=True,
            comment="SSO側で管理されている表示名",
        ),
        # Timestamps
        sa.Column(
            "last_sso_login",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最終SSO経由ログイン日時",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="SSO連携作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="SSO連携更新日時",
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint("id"),
        # Unique constraints
        sa.UniqueConstraint(
            "sso_subject_id", "sso_provider", name="uq_user_sso_subject_provider"
        ),
        sa.UniqueConstraint(
            "user_id", "sso_provider", name="uq_user_sso_user_provider"
        ),
        # Foreign key constraint
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for performance optimization
    op.create_index("ix_user_sso_subject_id", "user_sso", ["sso_subject_id"])
    op.create_index("ix_user_sso_provider", "user_sso", ["sso_provider"])
    op.create_index("ix_user_sso_user_id", "user_sso", ["user_id"])
    op.create_index("ix_user_sso_last_login", "user_sso", ["last_sso_login"])


def downgrade() -> None:
    """
    Remove user_sso table and related indexes
    """
    # Drop indexes first
    op.drop_index("ix_user_sso_last_login", table_name="user_sso")
    op.drop_index("ix_user_sso_user_id", table_name="user_sso")
    op.drop_index("ix_user_sso_provider", table_name="user_sso")
    op.drop_index("ix_user_sso_subject_id", table_name="user_sso")

    # Drop table
    op.drop_table("user_sso")
