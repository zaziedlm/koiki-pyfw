# 技術スタック

## バックエンド

- **Python**: >=3.11.7
- **FastAPI**: ASGI Webフレームワーク
- **Uvicorn**: ASGIサーバー
- **uv**: 依存同期とコマンド実行
- **uv.lock**: lockfile 正本
- **SQLAlchemy 2.0**: 非同期ORM
- **Alembic**: マイグレーション管理
- **PostgreSQL / SQLite**: 本番・開発/テストDB

## パッケージ構成

- `components/libkoiki`: reusable framework package
- `components/koiki_ref_app`: reference application package
- `app`: legacy compatibility wrapper
- `frontend`: Next.js frontend starter

## よく使うコマンド

```bash
uv sync --locked
uv run --locked uvicorn koiki_ref_app.asgi:app --reload --port 8000
uv run --locked pytest
uv run --locked alembic upgrade head
uv sync --locked --group security
uv run --locked pip-audit
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src
```

`app.main:app` は互換導線としてのみ扱う。

## フロントエンド

- **Next.js**: App Router
- **React**
- **TypeScript**
- **Tailwind CSS**
- **TanStack Query**
- **Zustand**

```bash
cd frontend
npm run dev
npm run build
npm run lint
```
