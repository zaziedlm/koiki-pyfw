"""Create the vNext database baseline with ownership-based table names.

Revision ID: 20260715001
Revises: None
Create Date: 2026-07-15

This temporary M1 baseline preserves the pre-vNext physical schema semantics
while replacing KOIKI-FW-managed table names. It intentionally retains the
business-clock initial row; DB-06 moves that responsibility to bootstrap seed.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260715001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "koiki_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_koiki_permissions_id", "koiki_permissions", ["id"])
    op.create_index(
        "ix_koiki_permissions_name", "koiki_permissions", ["name"], unique=True
    )
    op.create_index(
        "ix_koiki_permissions_resource", "koiki_permissions", ["resource"]
    )
    op.create_index(
        "ix_koiki_permissions_action", "koiki_permissions", ["action"]
    )

    op.create_table(
        "koiki_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_koiki_roles_id", "koiki_roles", ["id"])
    op.create_index("ix_koiki_roles_name", "koiki_roles", ["name"], unique=True)

    op.create_table(
        "koiki_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_koiki_users_id", "koiki_users", ["id"])
    op.create_index("ix_koiki_users_username", "koiki_users", ["username"], unique=True)
    op.create_index("ix_koiki_users_email", "koiki_users", ["email"], unique=True)
    op.create_index("ix_koiki_users_full_name", "koiki_users", ["full_name"])

    op.create_table(
        "koiki_role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["koiki_roles.id"], name="fk_koiki_role_permissions_role"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["koiki_permissions.id"],
            name="fk_koiki_role_permissions_permission",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "koiki_user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["koiki_users.id"], name="fk_koiki_user_roles_user"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["koiki_roles.id"], name="fk_koiki_user_roles_role"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "koiki_todos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["koiki_users.id"],
            name="fk_koiki_todos_owner",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_koiki_todos_id", "koiki_todos", ["id"])
    op.create_index("ix_koiki_todos_title", "koiki_todos", ["title"])
    op.create_index("ix_koiki_todos_owner_id", "koiki_todos", ["owner_id"])

    op.create_table(
        "koiki_refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["koiki_users.id"],
            name="fk_koiki_refresh_tokens_user",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_koiki_refresh_tokens_id", "koiki_refresh_tokens", ["id"])
    op.create_index(
        "ix_koiki_refresh_tokens_user_id", "koiki_refresh_tokens", ["user_id"]
    )
    op.create_index(
        "ix_koiki_refresh_tokens_token_hash",
        "koiki_refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_koiki_refresh_tokens_expires_at", "koiki_refresh_tokens", ["expires_at"]
    )
    op.create_index(
        "ix_koiki_refresh_tokens_is_revoked",
        "koiki_refresh_tokens",
        ["is_revoked"],
    )

    op.create_table(
        "koiki_password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["koiki_users.id"],
            name="fk_koiki_password_reset_tokens_user",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_koiki_password_reset_tokens_id", "koiki_password_reset_tokens", ["id"]
    )
    op.create_index(
        "ix_koiki_password_reset_tokens_user_id",
        "koiki_password_reset_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_koiki_password_reset_tokens_token_hash",
        "koiki_password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_koiki_password_reset_tokens_expires_at",
        "koiki_password_reset_tokens",
        ["expires_at"],
    )
    op.create_index(
        "ix_koiki_password_reset_tokens_is_used",
        "koiki_password_reset_tokens",
        ["is_used"],
    )

    op.create_table(
        "koiki_login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("is_successful", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=100), nullable=True),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["koiki_users.id"],
            name="fk_koiki_login_attempts_user",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_koiki_login_attempts_id", "koiki_login_attempts", ["id"])
    op.create_index(
        "ix_koiki_login_attempts_email", "koiki_login_attempts", ["email"]
    )
    op.create_index(
        "ix_koiki_login_attempts_user_id", "koiki_login_attempts", ["user_id"]
    )
    op.create_index(
        "ix_koiki_login_attempts_ip_address", "koiki_login_attempts", ["ip_address"]
    )
    op.create_index(
        "ix_koiki_login_attempts_is_successful",
        "koiki_login_attempts",
        ["is_successful"],
    )
    op.create_index(
        "ix_koiki_login_attempts_attempted_at",
        "koiki_login_attempts",
        ["attempted_at"],
    )

    op.create_table(
        "kkref_user_sso_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sso_subject_id", sa.String(length=255), nullable=False),
        sa.Column(
            "sso_provider",
            sa.String(length=50),
            server_default=sa.text("'oidc'"),
            nullable=False,
        ),
        sa.Column("sso_email", sa.String(length=255), nullable=True),
        sa.Column("sso_display_name", sa.String(length=100), nullable=True),
        sa.Column("last_sso_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["koiki_users.id"],
            name="fk_kkref_user_sso_links_user",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "sso_subject_id",
            "sso_provider",
            name="uq_kkref_user_sso_links_subject_provider",
        ),
        sa.UniqueConstraint(
            "user_id",
            "sso_provider",
            name="uq_kkref_user_sso_links_user_provider",
        ),
    )
    op.create_index(
        "ix_kkref_user_sso_links_subject_id",
        "kkref_user_sso_links",
        ["sso_subject_id"],
    )
    op.create_index(
        "ix_kkref_user_sso_links_provider", "kkref_user_sso_links", ["sso_provider"]
    )
    op.create_index(
        "ix_kkref_user_sso_links_user_id", "kkref_user_sso_links", ["user_id"]
    )
    op.create_index(
        "ix_kkref_user_sso_links_last_login",
        "kkref_user_sso_links",
        ["last_sso_login"],
    )

    op.create_table(
        "kkref_saml_auth_flows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.String(length=255), nullable=True),
        sa.Column("relay_nonce", sa.String(length=255), nullable=False),
        sa.Column(
            "sso_provider",
            sa.String(length=50),
            server_default=sa.text("'saml'"),
            nullable=False,
        ),
        sa.Column("redirect_uri", sa.String(length=2048), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("subject_id", sa.String(length=255), nullable=True),
        sa.Column("session_index", sa.String(length=512), nullable=True),
        sa.Column("ticket_id", sa.String(length=255), nullable=True),
        sa.Column("relay_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_ticket_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'authn_requested'"),
            nullable=False,
        ),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["koiki_users.id"],
            name="fk_kkref_saml_auth_flows_user",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("ticket_id", name="uq_kkref_saml_auth_flows_ticket_id"),
        sa.UniqueConstraint(
            "relay_nonce", name="uq_kkref_saml_auth_flows_relay_nonce"
        ),
    )
    op.create_index(
        "ix_kkref_saml_auth_flows_status", "kkref_saml_auth_flows", ["status"]
    )
    op.create_index(
        "ix_kkref_saml_auth_flows_ticket_id", "kkref_saml_auth_flows", ["ticket_id"]
    )
    op.create_index(
        "ix_kkref_saml_auth_flows_relay_nonce",
        "kkref_saml_auth_flows",
        ["relay_nonce"],
    )
    op.create_index(
        "ix_kkref_saml_auth_flows_user_id", "kkref_saml_auth_flows", ["user_id"]
    )
    op.create_index(
        "ix_kkref_saml_auth_flows_status_expires",
        "kkref_saml_auth_flows",
        ["status", "login_ticket_expires_at"],
    )

    op.create_table(
        "kkbiz_business_clock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "mode",
            sa.String(length=16),
            server_default=sa.text("'REALTIME'"),
            nullable=False,
        ),
        sa.Column(
            "base_timezone",
            sa.String(length=64),
            server_default=sa.text("'Asia/Tokyo'"),
            nullable=False,
        ),
        sa.Column("frozen_business_date", sa.Date(), nullable=True),
        sa.Column("frozen_business_time", sa.Time(), nullable=True),
        sa.Column(
            "offset_days", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "offset_minutes", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "updated_by",
            sa.String(length=255),
            server_default=sa.text("'system'"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_kkbiz_business_clock_singleton"),
    )
    op.execute(
        """
        INSERT INTO kkbiz_business_clock
            (id, mode, base_timezone, offset_days, offset_minutes, version, updated_by)
        VALUES
            (1, 'REALTIME', 'Asia/Tokyo', 0, 0, 1, 'system')
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("kkbiz_business_clock")
    op.drop_table("kkref_saml_auth_flows")
    op.drop_table("kkref_user_sso_links")
    op.drop_table("koiki_login_attempts")
    op.drop_table("koiki_password_reset_tokens")
    op.drop_table("koiki_refresh_tokens")
    op.drop_table("koiki_todos")
    op.drop_table("koiki_user_roles")
    op.drop_table("koiki_role_permissions")
    op.drop_table("koiki_users")
    op.drop_table("koiki_roles")
    op.drop_table("koiki_permissions")
