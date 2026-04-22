# app/models/saml_auth_flow.py
"""
SAML認証フローモデル

SAML認証の状態をDBで管理し、複数コンテナ環境での
チケット二重使用防止・relay_state整合性検証を実現する。
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
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

    __tablename__ = "saml_auth_flow"

    # --- AuthnRequest時に記録 ---
    request_id = Column(
        String(255),
        nullable=True,
        comment="SAML AuthnRequest ID (_req)",
    )

    relay_nonce = Column(
        String(255),
        nullable=False,
        comment="RelayState内のnonce（フロー一意性保証）",
    )

    sso_provider = Column(
        String(50),
        nullable=False,
        default="saml",
        comment="SSOプロバイダー識別子",
    )

    redirect_uri = Column(
        String(2048),
        nullable=True,
        comment="認証完了後のリダイレクト先URI",
    )

    # --- ACS時に記録 ---
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="認証されたローカルユーザーID",
    )

    subject_id = Column(
        String(255),
        nullable=True,
        comment="SAML Subject ID（nameID）",
    )

    session_index = Column(
        String(512),
        nullable=True,
        comment="IdPセッションインデックス",
    )

    ticket_id = Column(
        String(255),
        nullable=True,
        comment="ログインチケット識別子",
    )

    # --- 有効期限 ---
    relay_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="RelayStateの有効期限",
    )

    login_ticket_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="ログインチケットの有効期限",
    )

    # --- 状態管理 ---
    status = Column(
        String(30),
        nullable=False,
        default="authn_requested",
        comment="フロー状態: authn_requested / acs_verified / ticket_consumed",
    )

    consumed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="チケット消費日時",
    )

    # --- インデックスと制約 ---
    __table_args__ = (
        # ticket_idはユニーク（二重使用防止の要）
        UniqueConstraint("ticket_id", name="uq_saml_auth_flow_ticket_id"),
        # relay_nonceもユニーク（フロー一意性保証）
        UniqueConstraint("relay_nonce", name="uq_saml_auth_flow_relay_nonce"),
        # 検索パフォーマンス用インデックス
        Index("ix_saml_auth_flow_status", "status"),
        Index("ix_saml_auth_flow_ticket_id", "ticket_id"),
        Index("ix_saml_auth_flow_relay_nonce", "relay_nonce"),
        Index("ix_saml_auth_flow_user_id", "user_id"),
        Index(
            "ix_saml_auth_flow_status_expires",
            "status",
            "login_ticket_expires_at",
        ),
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
