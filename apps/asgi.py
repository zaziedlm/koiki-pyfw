"""業務アプリ (apps/) の ASGI エントリポイント（サンプル skeleton）。

reference app を ``create_app()`` で生成し、apps/ 側の業務 router を
``include_router()`` で合成する。``components/`` を編集せずに業務 API を追加できる。
downstream はこのファイルを起点に業務 API を組み込む。

起動例::

    uv run --locked uvicorn apps.asgi:app --reload
"""

from koiki_ref_app.app_factory import create_app

from apps.api.v1.router import router as business_router

app = create_app()
app.include_router(business_router)
