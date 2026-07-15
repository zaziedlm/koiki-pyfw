"""Create the final vNext database baseline.

Revision ID: 20260715001
Revises: None
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260715001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "koiki_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("resource", sa.String(50)),
        sa.Column("action", sa.String(50)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_koiki_permissions"),
        sa.UniqueConstraint("name", name="uq_koiki_permissions_name"),
    )
    op.create_table(
        "koiki_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_koiki_roles"),
        sa.UniqueConstraint("name", name="uq_koiki_roles_name"),
    )
    op.create_table(
        "koiki_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String()), sa.Column("hashed_password", sa.String()), sa.Column("full_name", sa.String()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_koiki_users"),
        sa.UniqueConstraint("username", name="uq_koiki_users_username"),
        sa.UniqueConstraint("email", name="uq_koiki_users_email"),
    )
    op.create_table(
        "koiki_role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False), sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["koiki_roles.id"], name="fk_koiki_role_permissions_role_id_koiki_roles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["koiki_permissions.id"], name="fk_koiki_role_permissions_permission_id_koiki_permissions", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_koiki_role_permissions"),
    )
    op.create_index("ix_koiki_role_permissions_permission_id", "koiki_role_permissions", ["permission_id"])
    op.create_table(
        "koiki_user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["koiki_users.id"], name="fk_koiki_user_roles_user_id_koiki_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["koiki_roles.id"], name="fk_koiki_user_roles_role_id_koiki_roles", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_koiki_user_roles"),
    )
    op.create_index("ix_koiki_user_roles_role_id", "koiki_user_roles", ["role_id"])
    op.create_table(
        "koiki_todos",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False), sa.Column("owner_id", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("version >= 1", name="positive_version"),
        sa.ForeignKeyConstraint(["owner_id"], ["koiki_users.id"], name="fk_koiki_todos_owner_id_koiki_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_koiki_todos"),
    )
    op.create_index("ix_koiki_todos_owner_id_created_at_desc", "koiki_todos", ["owner_id", sa.text("created_at DESC")])
    op.create_table(
        "koiki_refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("is_revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("device_info", sa.Text()), *_timestamps(), sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["koiki_users.id"], name="fk_koiki_refresh_tokens_user_id_koiki_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_koiki_refresh_tokens"), sa.UniqueConstraint("token_hash", name="uq_koiki_refresh_tokens_token_hash"),
    )
    op.create_index("ix_koiki_refresh_tokens_user_id_created_at_desc", "koiki_refresh_tokens", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_koiki_refresh_tokens_active_user_id_expires_at", "koiki_refresh_tokens", ["user_id", "expires_at"], postgresql_where=sa.text("is_revoked IS false"))
    op.create_index("ix_koiki_refresh_tokens_expires_at", "koiki_refresh_tokens", ["expires_at"])
    op.create_table(
        "koiki_password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("is_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(), sa.Column("used_at", sa.DateTime(timezone=True)), sa.Column("ip_address", sa.String(45)), sa.Column("user_agent", sa.Text()),
        sa.ForeignKeyConstraint(["user_id"], ["koiki_users.id"], name="fk_koiki_password_reset_tokens_user_id_koiki_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_koiki_password_reset_tokens"), sa.UniqueConstraint("token_hash", name="uq_koiki_password_reset_tokens_token_hash"),
    )
    op.create_index("ix_koiki_password_reset_tokens_user_id", "koiki_password_reset_tokens", ["user_id"])
    op.create_index("ix_koiki_password_reset_tokens_active_user_id_expires_at", "koiki_password_reset_tokens", ["user_id", "expires_at"], postgresql_where=sa.text("is_used IS false"))
    op.create_index("ix_koiki_password_reset_tokens_expires_at", "koiki_password_reset_tokens", ["expires_at"])
    op.create_table(
        "koiki_login_attempts",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("user_id", sa.Integer()),
        sa.Column("ip_address", sa.String(45), nullable=False), sa.Column("user_agent", sa.Text()), sa.Column("is_successful", sa.Boolean(), nullable=False), sa.Column("failure_reason", sa.String(100)),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["koiki_users.id"], name="fk_koiki_login_attempts_user_id_koiki_users", ondelete="SET NULL"), sa.PrimaryKeyConstraint("id", name="pk_koiki_login_attempts"),
    )
    op.create_index("ix_koiki_login_attempts_failed_email_attempted_at_desc", "koiki_login_attempts", ["email", sa.text("attempted_at DESC")], postgresql_where=sa.text("is_successful IS false"))
    op.create_index("ix_koiki_login_attempts_failed_ip_address_attempted_at_desc", "koiki_login_attempts", ["ip_address", sa.text("attempted_at DESC")], postgresql_where=sa.text("is_successful IS false"))
    op.create_index("ix_koiki_login_attempts_success_email_attempted_at_desc", "koiki_login_attempts", ["email", sa.text("attempted_at DESC")], postgresql_where=sa.text("is_successful IS true"))
    op.create_index("ix_koiki_login_attempts_user_id", "koiki_login_attempts", ["user_id"])
    op.create_index("ix_koiki_login_attempts_attempted_at", "koiki_login_attempts", ["attempted_at"])
    op.create_table(
        "kkref_user_sso_links",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("sso_subject_id", sa.String(255), nullable=False),
        sa.Column("sso_provider", sa.String(50), server_default=sa.text("'oidc'"), nullable=False), sa.Column("sso_email", sa.String(255)), sa.Column("sso_display_name", sa.String(100)), sa.Column("last_sso_login", sa.DateTime(timezone=True)), *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["koiki_users.id"], name="fk_kkref_user_sso_links_user_id_koiki_users", ondelete="CASCADE"), sa.PrimaryKeyConstraint("id", name="pk_kkref_user_sso_links"),
        sa.UniqueConstraint("sso_subject_id", "sso_provider", name="uq_kkref_user_sso_links_sso_subject_id_sso_provider"), sa.UniqueConstraint("user_id", "sso_provider", name="uq_kkref_user_sso_links_user_id_sso_provider"),
    )
    op.create_index("ix_kkref_user_sso_links_user_id_last_sso_login_desc", "kkref_user_sso_links", ["user_id", sa.text("last_sso_login DESC")])
    op.create_index("ix_kkref_user_sso_links_sso_provider_last_sso_login_desc", "kkref_user_sso_links", ["sso_provider", sa.text("last_sso_login DESC")])
    op.create_index("ix_kkref_user_sso_links_recent_last_sso_login_desc", "kkref_user_sso_links", [sa.text("last_sso_login DESC")], postgresql_where=sa.text("last_sso_login IS NOT NULL"))
    op.create_table(
        "kkref_saml_auth_flows",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("request_id", sa.String(255)), sa.Column("relay_nonce", sa.String(255), nullable=False),
        sa.Column("sso_provider", sa.String(50), server_default=sa.text("'saml'"), nullable=False), sa.Column("redirect_uri", sa.String(2048)), sa.Column("user_id", sa.Integer()), sa.Column("subject_id", sa.String(255)), sa.Column("session_index", sa.String(512)), sa.Column("ticket_id", sa.String(255)),
        sa.Column("relay_expires_at", sa.DateTime(timezone=True)), sa.Column("login_ticket_expires_at", sa.DateTime(timezone=True)), sa.Column("status", sa.String(30), server_default=sa.text("'authn_requested'"), nullable=False), sa.Column("consumed_at", sa.DateTime(timezone=True)), *_timestamps(),
        sa.CheckConstraint("status IN ('authn_requested', 'acs_verified', 'ticket_consumed', 'expired')", name="valid_status"),
        sa.ForeignKeyConstraint(["user_id"], ["koiki_users.id"], name="fk_kkref_saml_auth_flows_user_id_koiki_users", ondelete="SET NULL"), sa.PrimaryKeyConstraint("id", name="pk_kkref_saml_auth_flows"),
        sa.UniqueConstraint("ticket_id", name="uq_kkref_saml_auth_flows_ticket_id"), sa.UniqueConstraint("relay_nonce", name="uq_kkref_saml_auth_flows_relay_nonce"),
    )
    op.create_index("ix_kkref_saml_auth_flows_authn_requested_relay_expires_at", "kkref_saml_auth_flows", ["relay_expires_at"], postgresql_where=sa.text("status = 'authn_requested'"))
    op.create_index("ix_kkref_saml_auth_flows_acs_verified_login_ticket_expires_at", "kkref_saml_auth_flows", ["login_ticket_expires_at"], postgresql_where=sa.text("status = 'acs_verified'"))
    op.create_index("ix_kkref_saml_auth_flows_terminal_updated_at", "kkref_saml_auth_flows", ["updated_at"], postgresql_where=sa.text("status IN ('expired', 'ticket_consumed')"))
    op.create_index("ix_kkref_saml_auth_flows_user_id", "kkref_saml_auth_flows", ["user_id"])
    op.create_index("ix_kkref_saml_flows_consumed_user_updated", "kkref_saml_auth_flows", ["user_id", sa.text("updated_at DESC")], postgresql_where=sa.text("status = 'ticket_consumed' AND session_index IS NOT NULL"))
    op.create_table(
        "kkbiz_business_clock",
        sa.Column("id", sa.Integer(), nullable=False), *_timestamps(),
        sa.Column("mode", sa.String(16), server_default=sa.text("'REALTIME'"), nullable=False), sa.Column("base_timezone", sa.String(64), server_default=sa.text("'Asia/Tokyo'"), nullable=False),
        sa.Column("frozen_business_date", sa.Date()), sa.Column("frozen_business_time", sa.Time()), sa.Column("offset_days", sa.Integer(), server_default=sa.text("0"), nullable=False), sa.Column("offset_minutes", sa.Integer(), server_default=sa.text("0"), nullable=False), sa.Column("comment", sa.Text()), sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False), sa.Column("updated_by", sa.String(255), server_default=sa.text("'system'"), nullable=False),
        sa.CheckConstraint("id = 1", name="singleton"), sa.CheckConstraint("version >= 1", name="positive_version"), sa.CheckConstraint("mode IN ('REALTIME', 'OFFSET', 'FROZEN')", name="valid_mode"), sa.CheckConstraint("(mode = 'FROZEN' AND frozen_business_date IS NOT NULL AND frozen_business_time IS NOT NULL) OR (mode != 'FROZEN' AND frozen_business_date IS NULL AND frozen_business_time IS NULL)", name="frozen_value_pair"),
        sa.PrimaryKeyConstraint("id", name="pk_kkbiz_business_clock"),
    )


def downgrade() -> None:
    for table in ("kkbiz_business_clock", "kkref_saml_auth_flows", "kkref_user_sso_links", "koiki_login_attempts", "koiki_password_reset_tokens", "koiki_refresh_tokens", "koiki_todos", "koiki_user_roles", "koiki_role_permissions", "koiki_users", "koiki_roles", "koiki_permissions"):
        op.drop_table(table)
