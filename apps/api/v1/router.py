"""業務アプリ固有 API の router 合成（サンプル skeleton）。

業務アプリ固有の router 登録は `apps/` 側で所有し、`components/` には置かない。
"""

from fastapi import APIRouter

from apps.api.v1.endpoints import sample

router = APIRouter(prefix="/business", tags=["business"])
router.include_router(sample.router)
