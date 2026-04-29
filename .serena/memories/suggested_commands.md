# 開発コマンド（Windows環境）

## 依存同期

```powershell
uv sync --locked
uv sync --locked --group dev --group test
```

## ローカル起動

```powershell
$env:APP_ENV = "development"
$env:DEBUG = "true"
uv run --locked alembic upgrade head
uv run --locked uvicorn koiki_ref_app.asgi:app --host 0.0.0.0 --port 8000 --reload
```

`app.main:app` は互換導線です。新規手順では `koiki_ref_app.asgi:app` を使います。

## テスト

```powershell
uv run --locked pytest
uv run --locked pytest components/libkoiki/tests
uv run --locked pytest components/koiki_ref_app/tests
uv run --locked pytest tests
```

DB integration は専用 helper を使います。

```powershell
.\scripts\run-db-integration-tests.ps1
```

## マイグレーション

```powershell
uv run --locked alembic revision --autogenerate -m "変更の説明"
uv run --locked alembic upgrade head
uv run --locked alembic history
uv run --locked alembic current
```

## セキュリティ監査

```powershell
uv sync --locked --group security
uv run --locked pip-audit
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src
```

## Docker

```powershell
docker compose up --build -d
docker compose logs -f app
docker compose down
```

## フロントエンド

```powershell
cd frontend
npm install
npm run dev
npm run build
npm run lint
```
