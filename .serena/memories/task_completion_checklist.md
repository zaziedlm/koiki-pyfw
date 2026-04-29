# タスク完了時のチェックリスト

## 基本

- 変更範囲に応じた最小のテストを実行する
- framework 変更は `components/libkoiki/tests` を優先する
- reference app 変更は `components/koiki_ref_app/tests` を優先する
- shared / cross-component 変更は root `tests` または統合テストで確認する

## Python

```powershell
uv sync --locked --group dev --group test
uv run --locked pytest
uv run --locked pytest components/libkoiki/tests
uv run --locked pytest components/koiki_ref_app/tests
```

## マイグレーション

```powershell
uv run --locked alembic current
uv run --locked alembic upgrade head
```

モデル変更時は migration 生成と SQL 内容を確認します。

```powershell
uv run --locked alembic revision --autogenerate -m "変更内容"
uv run --locked alembic upgrade head --sql
```

## セキュリティ

```powershell
uv sync --locked --group security
uv run --locked pip-audit
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src
```

## フロントエンド

```powershell
cd frontend
npm run lint
npm run build
```

## 起動確認

```powershell
uv run --locked uvicorn koiki_ref_app.asgi:app --host 0.0.0.0 --port 8000 --reload
```

`app.main:app` は互換 wrapper の確認時だけ使います。
