from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base

# user_roles テーブルの関連付け（多対多）
user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),  # 'user' ではなく 'users' を参照
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class UserModel(Base):
    __tablename__ = "users"  # テーブル名を "user" から "users" に変更
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # todos = relationship("TodoModel", back_populates="user")
    todos = relationship("TodoModel", back_populates="owner", cascade="all, delete-orphan")
    # ロールとの関係
    roles = relationship("RoleModel", secondary=user_roles, back_populates="users")