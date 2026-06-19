"""業務アプリ固有モデルのサンプル（型のひな形）。

業務モデルは reference app と同じ ``koiki_ref_app.db.base.Base`` を継承する。
この Base は ``libkoiki.db.base.Base`` の registry / metadata を共有するため、
apps/ のモデルも統一された migration 体系に乗り、id / created_at / updated_at と
スネークケースの ``__tablename__`` を自動的に得る。

別の主キー構造や ``tenant_id`` 等が必要な場合は、``components/`` を編集せず、
apps/ 側で ``libkoiki.db.base.Base`` の registry を共有する独自 Base を定義する。

注意: これはサンプルである。``apps/asgi.py`` からは import されないため、
明示的に import しない限り共有 metadata にテーブルは登録されない。
実装時はこの型をコピーし、不要なら削除する。
"""

from sqlalchemy import Column, String

from koiki_ref_app.db.base import Base


class SampleBusinessItem(Base):
    """サンプル業務モデル。downstream はこの型をコピーして利用する。"""

    name = Column(String(length=255), nullable=False)
