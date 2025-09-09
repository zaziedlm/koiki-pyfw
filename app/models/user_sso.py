# app/models/user_sso.py
"""
SSO連携ユーザーモデル

外部SSOサービス（OpenID Connect等）とローカルユーザーの
連携情報を管理するSQLAlchemyモデルを定義
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base


class UserSSO(Base):
    """
    ユーザーSSO連携モデル
    
    外部SSOサービスでの一意識別子（sub）とローカルユーザーを関連付け。
    一人のユーザーが複数のSSOプロバイダーと連携可能な設計。
    """
    __tablename__ = "user_sso"

    id = Column(Integer, primary_key=True, index=True)
    
    # ローカルユーザーとの関連
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        comment="連携するローカルユーザーID"
    )
    
    # SSOサービス識別情報
    sso_subject_id = Column(
        String(255), 
        nullable=False, 
        comment="SSOサービスでの一意識別子 (sub claim)"
    )
    
    sso_provider = Column(
        String(50), 
        nullable=False, 
        default="oidc",
        comment="SSOプロバイダー識別子"
    )
    
    # 連携メタデータ
    sso_email = Column(
        String(255),
        nullable=True,
        comment="SSO側で管理されているメールアドレス"
    )
    
    sso_display_name = Column(
        String(100),
        nullable=True,
        comment="SSO側で管理されている表示名"
    )
    
    # タイムスタンプ
    last_sso_login = Column(
        DateTime,
        nullable=True,
        comment="最終SSO経由ログイン日時"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="SSO連携作成日時"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="SSO連携更新日時"
    )

    # リレーションシップ
    user = relationship("UserModel", back_populates="sso_links")

    # インデックスと制約
    __table_args__ = (
        # sso_subject_id + sso_provider の組み合わせで一意制約
        UniqueConstraint(
            "sso_subject_id", 
            "sso_provider", 
            name="uq_user_sso_subject_provider"
        ),
        
        # user_id + sso_provider の組み合わせで一意制約
        # （同一ユーザーが同一プロバイダーで複数連携することを防ぐ）
        UniqueConstraint(
            "user_id",
            "sso_provider", 
            name="uq_user_sso_user_provider"
        ),
        
        # 検索パフォーマンス向上のためのインデックス
        Index("ix_user_sso_subject_id", "sso_subject_id"),
        Index("ix_user_sso_provider", "sso_provider"),
        Index("ix_user_sso_user_id", "user_id"),
        Index("ix_user_sso_last_login", "last_sso_login"),
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
        self.last_sso_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()

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
        self.updated_at = datetime.utcnow()