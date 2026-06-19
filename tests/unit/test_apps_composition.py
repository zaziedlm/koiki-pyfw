"""apps/ 業務アプリ composition の最小 smoke テスト。

downstream の `apps/asgi.py` が reference app を `create_app()` で生成し、
業務 router を合成できること、業務モデルが `koiki_ref_app.db.base.Base` の
共有 registry に乗ることを固定する。
"""

from __future__ import annotations


def test_apps_asgi_composes_reference_app_and_business_router() -> None:
    from apps.asgi import app

    paths = {getattr(route, "path", "") for route in app.routes}
    # business router が合成されている
    assert "/business/items" in paths
    # reference app の API router も維持されている
    assert any(path.startswith("/api/v1") for path in paths)


def test_business_model_shares_libkoiki_registry_via_refapp_base() -> None:
    from koiki_ref_app.db.base import Base
    from apps.models.sample import SampleBusinessItem

    # reference app と同じ Base / metadata を共有する
    assert SampleBusinessItem.metadata is Base.metadata
    # スネークケースの __tablename__ と共通カラムを継承する
    assert SampleBusinessItem.__tablename__ == "sample_business_item"
    columns = {column.name for column in SampleBusinessItem.__table__.columns}
    assert {"id", "created_at", "updated_at", "name"}.issubset(columns)
