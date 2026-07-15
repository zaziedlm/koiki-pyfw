# app/models/user_sso.py
"""
SSO連携ユーザーモデル

外部SSOサービス（OpenID Connect等）とローカルユーザーの
連携情報を管理するSQLAlchemyモデルを定義
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
    text,
)
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base
from libkoiki.models.user import UserModel


class UserSSO(Base):
    """
    ユーザーSSO連携モデル

    外部SSOサービスでの一意識別子（sub）とローカルユーザーを関連付け。
    一人のユーザーが複数のSSOプロバイダーと連携可能な設計。
    """

    __tablename__ = "kkref_user_sso_links"

    # ローカルユーザーとの関連
    user_id = Column(
        Integer,
        ForeignKey("koiki_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # SSOサービス識別情報
    sso_subject_id = Column(
        String(255), nullable=False
    )

    sso_provider = Column(
        String(50), nullable=False, default="oidc", server_default=text("'oidc'")
    )

    # 連携メタデータ
    sso_email = Column(
        String(255), nullable=True
    )

    sso_display_name = Column(
        String(100), nullable=True
    )

    # タイムスタンプ
    last_sso_login = Column(
        DateTime(timezone=True), nullable=True
    )

    # リレーションシップ
    user = relationship(UserModel, back_populates="sso_links")

    # インデックスと制約
    __table_args__ = (
        # sso_subject_id + sso_provider の組み合わせで一意制約
        UniqueConstraint("sso_subject_id", "sso_provider"),
        # user_id + sso_provider の組み合わせで一意制約
        # （同一ユーザーが同一プロバイダーで複数連携することを防ぐ）
        UniqueConstraint("user_id", "sso_provider"),
        # 検索パフォーマンス向上のためのインデックス
        Index("ix_kkref_user_sso_links_user_id_last_sso_login_desc", user_id, last_sso_login.desc()),
        Index("ix_kkref_user_sso_links_sso_provider_last_sso_login_desc", sso_provider, last_sso_login.desc()),
        Index("ix_kkref_user_sso_links_recent_last_sso_login_desc", last_sso_login.desc(), postgresql_where=last_sso_login.is_not(None), sqlite_where=last_sso_login.is_not(None)),
    )

    def __repr__(self) -> str:
        return (
            f"<UserSSO(id={self.id}, "
            f"user_id={self.user_id}, "
            f"provider={self.sso_provider}, "
            f"subject_id={self.sso_subject_id[:20]}...)>"
        )

    def update_login_timestamp(self) -> None:
        """
        最終SSO ログイン日時を現在時刻に更新
        """
        now = datetime.now(timezone.utc)
        self.last_sso_login = now
        self.updated_at = now

    def update_sso_info(self, email: str = None, display_name: str = None) -> None:
        """
        SSO側から取得した情報でメタデータを更新

        Args:
            email: SSO側のメールアドレス
            display_name: SSO側の表示名
        """
        if email is not None:
            self.sso_email = email
        if display_name is not None:
            self.sso_display_name = display_name
        self.updated_at = datetime.now(timezone.utc)
