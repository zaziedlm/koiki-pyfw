"""add saml_auth_flow table

Revision ID: 20260228001
Revises: 20251030001_rename_business_clock_table
Create Date: 2026-02-28 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260228001"
down_revision: Union[str, None] = "20251030001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saml_auth_flow",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "request_id",
            sa.String(255),
            nullable=True,
            comment="SAML AuthnRequest ID",
        ),
        sa.Column(
            "relay_nonce",
            sa.String(255),
            nullable=False,
            comment="RelayState内のnonce",
        ),
        sa.Column(
            "sso_provider",
            sa.String(50),
            nullable=False,
            server_default="saml",
            comment="SSOプロバイダー識別子",
        ),
        sa.Column(
            "redirect_uri",
            sa.String(2048),
            nullable=True,
            comment="認証完了後のリダイレクト先URI",
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="認証されたローカルユーザーID",
        ),
        sa.Column(
            "subject_id",
            sa.String(255),
            nullable=True,
            comment="SAML Subject ID",
        ),
        sa.Column(
            "session_index",
            sa.String(512),
            nullable=True,
            comment="IdPセッションインデックス",
        ),
        sa.Column(
            "ticket_id",
            sa.String(255),
            nullable=True,
            comment="ログインチケット識別子",
        ),
        sa.Column(
            "relay_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="RelayStateの有効期限",
        ),
        sa.Column(
            "login_ticket_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="ログインチケットの有効期限",
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="authn_requested",
            comment="フロー状態",
        ),
        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="チケット消費日時",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ユニーク制約
    op.create_unique_constraint(
        "uq_saml_auth_flow_ticket_id", "saml_auth_flow", ["ticket_id"]
    )
    op.create_unique_constraint(
        "uq_saml_auth_flow_relay_nonce", "saml_auth_flow", ["relay_nonce"]
    )

    # インデックス
    op.create_index("ix_saml_auth_flow_status", "saml_auth_flow", ["status"])
    op.create_index("ix_saml_auth_flow_ticket_id", "saml_auth_flow", ["ticket_id"])
    op.create_index(
        "ix_saml_auth_flow_relay_nonce", "saml_auth_flow", ["relay_nonce"]
    )
    op.create_index("ix_saml_auth_flow_user_id", "saml_auth_flow", ["user_id"])
    op.create_index(
        "ix_saml_auth_flow_status_expires",
        "saml_auth_flow",
        ["status", "login_ticket_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_saml_auth_flow_status_expires", table_name="saml_auth_flow")
    op.drop_index("ix_saml_auth_flow_user_id", table_name="saml_auth_flow")
    op.drop_index("ix_saml_auth_flow_relay_nonce", table_name="saml_auth_flow")
    op.drop_index("ix_saml_auth_flow_ticket_id", table_name="saml_auth_flow")
    op.drop_index("ix_saml_auth_flow_status", table_name="saml_auth_flow")
    op.drop_constraint(
        "uq_saml_auth_flow_relay_nonce", "saml_auth_flow", type_="unique"
    )
    op.drop_constraint(
        "uq_saml_auth_flow_ticket_id", "saml_auth_flow", type_="unique"
    )
    op.drop_table("saml_auth_flow")
