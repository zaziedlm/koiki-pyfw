# src/models/todo.py
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base
from libkoiki.models.user import UserModel # ownerとのリレーション用

class TodoModel(Base):
    __tablename__ = 'todos' # テーブル名

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False, server_default='false')

    # 所有者 (User) への外部キー
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Userモデルとのリレーション (Todo側から所有者Userを参照)
    owner: UserModel = relationship("UserModel", back_populates="todos")

    def __repr__(self):
        status = "Completed" if self.is_completed else "Pending"
        return f"<Todo(id={self.id}, title='{self.title[:20]}...', status='{status}', owner_id={self.owner_id})>"

# UserModel 側にもリレーションを追加する必要あり (user.py を修正)
# class UserModel(Base):
#     ...
#     todos: List["TodoModel"] = relationship("TodoModel", back_populates="owner", cascade="all, delete-orphan")
#     ...
