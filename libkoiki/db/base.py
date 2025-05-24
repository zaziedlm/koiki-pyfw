# src/db/base.py
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime, func
from typing import Any
import re # テーブル名変換用

# レガシーモードと共通機能を組み合わせたBaseクラス
class CustomBase:
    # SQLAlchemy 2.0の型アノテーション制約を無視する設定
    __allow_unmapped__ = True

    # テーブル名をクラス名からスネークケースに自動変換 (例: UserModel -> users)
    @declared_attr
    def __tablename__(cls) -> str:
        # クラス名から "Model" サフィックスを除去し、スネークケースに変換
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        # もし末尾が "_model" なら削除
        if name.endswith("_model"):
            name = name[:-len("_model")]
        return name

    # 共通カラム (主キー、作成日時、更新日時)
    id = Column(Integer, primary_key=True, index=True)
    # タイムゾーン対応のDateTime型を使用し、DBサーバーのデフォルトタイムゾーン/関数を利用
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(), # DBサーバーの現在時刻
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(), # レコード更新時にDBサーバーの現在時刻で更新
        nullable=False
    )

# 1つの統合されたBaseクラスを使用
Base = declarative_base(cls=CustomBase)