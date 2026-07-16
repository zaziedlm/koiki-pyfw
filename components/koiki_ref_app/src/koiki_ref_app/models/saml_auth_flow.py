# app/models/saml_auth_flow.py
"""
SAML認証フローモデル

SAML認証の状態をDBで管理し、複数コンテナ環境での
チケット二重使用防止・relay_state整合性検証を実現する。
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)

from libkoiki.db.base import Base


class SamlAuthFlow(Base):
    """
    SAML認証フロー状態管理テーブル

    認証フローのライフサイクルを追跡:
      authn_requested → acs_verified → ticket_consumed

    複数プロセス/コンテナ間でのチケット二重使用防止を
    DBレベルのユニーク制約と行ロックで保証する。
    """

    __tablename__ = "kkref_saml_auth_flows"

    # --- AuthnRequest時に記録 ---
    request_id = Column(
        String(255),
        nullable=True,
    )

    relay_nonce = Column(
        String(255),
        nullable=False,
    )

    sso_provider = Column(
        String(50),
        nullable=False,
        default="saml",
        server_default=text("'saml'"),
    )

    redirect_uri = Column(
        String(2048),
        nullable=True,
    )

    # --- ACS時に記録 ---
    user_id = Column(
        Integer,
        ForeignKey("koiki_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    subject_id = Column(
        String(255),
        nullable=True,
    )

    session_index = Column(
        String(512),
        nullable=True,
    )

    ticket_id = Column(
        String(255),
        nullable=True,
    )

    # --- 有効期限 ---
    relay_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    login_ticket_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- 状態管理 ---
    status = Column(
        String(30),
        nullable=False,
        default="authn_requested",
        server_default=text("'authn_requested'"),
    )

    consumed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- インデックスと制約 ---
    __table_args__ = (
        # ticket_idはユニーク（二重使用防止の要）
        UniqueConstraint("ticket_id"),
        # relay_nonceもユニーク（フロー一意性保証）
        UniqueConstraint("relay_nonce"),
        # 検索パフォーマンス用インデックス
        CheckConstraint("status IN ('authn_requested', 'acs_verified', 'ticket_consumed', 'expired')", name="valid_status"),
        Index("ix_kkref_saml_auth_flows_authn_requested_relay_expires_at", relay_expires_at, postgresql_where=status == "authn_requested", sqlite_where=status == "authn_requested"),
        Index("ix_kkref_saml_auth_flows_acs_verified_login_ticket_expires_at", login_ticket_expires_at, postgresql_where=status == "acs_verified", sqlite_where=status == "acs_verified"),
        Index("ix_kkref_saml_auth_flows_terminal_updated_at", text("updated_at"), postgresql_where=status.in_(("expired", "ticket_consumed")), sqlite_where=status.in_(("expired", "ticket_consumed"))),
        Index("ix_kkref_saml_auth_flows_user_id", user_id),
        Index("ix_kkref_saml_flows_consumed_user_updated", user_id, text("updated_at DESC"), postgresql_where=(status == "ticket_consumed") & session_index.is_not(None), sqlite_where=(status == "ticket_consumed") & session_index.is_not(None)),
    )

    def __repr__(self) -> str:
        return (
            f"<SamlAuthFlow(id={self.id}, "
            f"status={self.status}, "
            f"ticket_id={self.ticket_id[:12] + '...' if self.ticket_id else None})>"
        )

    def mark_acs_verified(
        self,
        *,
        user_id: int,
        subject_id: str,
        session_index: str | None,
        ticket_id: str,
        login_ticket_expires_at: datetime,
    ) -> None:
        """ACS検証完了を記録"""
        self.status = "acs_verified"
        self.user_id = user_id
        self.subject_id = subject_id
        self.session_index = session_index
        self.ticket_id = ticket_id
        self.login_ticket_expires_at = login_ticket_expires_at
        self.updated_at = datetime.now(timezone.utc)

    def mark_ticket_consumed(self) -> None:
        """チケット消費を記録"""
        now = datetime.now(timezone.utc)
        self.status = "ticket_consumed"
        self.consumed_at = now
        self.updated_at = now
