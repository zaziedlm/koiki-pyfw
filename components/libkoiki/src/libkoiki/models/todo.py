# src/models/todo.py
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base
from libkoiki.models.user import UserModel # ownerとのリレーション用

class TodoModel(Base):
    __tablename__ = "koiki_todos"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False, server_default=text("false"))

    # 楽観ロック用のバージョン番号 (アトミックUPDATEでのみインクリメントする)
    version = Column(Integer, default=1, nullable=False, server_default=text("1"))

    # 所有者 (User) への外部キー
    owner_id = Column(
        Integer,
        ForeignKey("koiki_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Userモデルとのリレーション (Todo側から所有者Userを参照)
    owner: UserModel = relationship("UserModel", back_populates="todos")

    __table_args__ = (
        CheckConstraint("version >= 1", name="positive_version"),
        Index("ix_koiki_todos_owner_id_created_at_desc", owner_id, text("created_at DESC")),
    )

    def __repr__(self):
        status = "Completed" if self.is_completed else "Pending"
        return f"<Todo(id={self.id}, title='{self.title[:20]}...', status='{status}', owner_id={self.owner_id})>"

# UserModel 側にもリレーションを追加する必要あり (user.py を修正)
# class UserModel(Base):
#     ...
#     todos: List["TodoModel"] = relationship("TodoModel", back_populates="owner", cascade="all, delete-orphan")
#     ...
