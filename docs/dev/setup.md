# Dev Setup

標準の Python 依存管理は `uv` です。

```bash
uv sync
uv run uvicorn koiki_ref_app.asgi:app --reload
```

互換導線として `app.main:app` も残っていますが、新規起動手順では `koiki_ref_app.asgi:app` を使います。

```bash
uv run --locked uvicorn koiki_ref_app.asgi:app --reload
```

詳細は `docs/dev/local_setup.md` を参照してください。
