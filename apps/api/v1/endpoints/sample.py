"""業務アプリ固有エンドポイントのサンプル。

downstream はこの型をコピーして案件固有 API を実装する。
DB を使う場合は `apps/services/` と `apps/repositories/` を介し、
モデルは `koiki_ref_app.db.base.Base` を継承する（`apps/models/sample.py` 参照）。
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/items")
async def list_items() -> list[dict]:
    """サンプル: 業務アイテム一覧を返す（静的データ）。"""
    return []
