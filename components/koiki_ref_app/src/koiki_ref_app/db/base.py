# app/db/base.py
"""
アプリケーション固有のモデル向け Declarative Base を提供するモジュール。

主な特徴:
- libkoiki 側の registry / metadata を共有しつつ、アプリ側で独自の共通カラム
  （主キーやタイムスタンプなど）を定義できる土台を用意。
- ライブラリ側の `CustomBase` が提供する既定カラムに依存しないため、アプリ要件に合わせて
  主キーの構造や監査項目を柔軟に設計可能。
"""

import re

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.orm import declared_attr

from libkoiki.db.base import Base as LibBase


class AppCustomBase:
    __abstract__ = True
    __allow_unmapped__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        """クラス名からテーブル名をスネークケースに変換"""
        name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        if name.endswith("_model"):
            name = name[: -len("_model")]
        return name

    # アプリ共通のカラム定義（必要に応じて調整可能）
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# libkoiki 側と同じ registry/metadata を共有した Base を生成
Base = LibBase.registry.generate_base(cls=AppCustomBase)

__all__ = ["Base"]
