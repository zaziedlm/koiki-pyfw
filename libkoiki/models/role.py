from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column

from libkoiki.db.base import Base

class RoleModel(Base):
    __tablename__ = "roles"
    
    # SQLAlchemy 2.0形式の型アノテーションに変更
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # users リレーションシップは user.py の backref で定義されているため省略可能