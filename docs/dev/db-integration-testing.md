# DB Integration Testing

`db_integration` マーカー付きテストは、標準 CI では実行しません。
PostgreSQL を用意したローカル Docker 環境で、明示的に実行してください。

## Run Locally

ローカルマシンから Docker Compose の PostgreSQL に接続する場合、DB host は `localhost` です。
`db` は Compose ネットワーク内のサービス名なので、ホスト側の `uv run ...` や pytest からは使わないでください。

```bash
export RUN_DB_INTEGRATION=1
export DATABASE_URL=postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
export ENV_FILE=.env.ci

uv run pytest \
  components/koiki_ref_app/tests/integration/app/api/test_auth_api.py \
  tests/integration/services/ \
  -m db_integration
```

## Alembic

Alembic の正規設定ファイルは `components/koiki_ref_app/alembic.ini` です。
root から実行する場合は、必ず `-c` で明示してください。

ホスト側から実行する例:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db"
uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
```

Docker Compose の app コンテナ内から実行する場合は、Compose ネットワーク上の `db` host を使います。

```bash
docker compose exec -T app alembic -c /app/components/koiki_ref_app/alembic.ini current
```

## PowerShell Helper

Windows PowerShell では、起動済みの PostgreSQL コンテナに対して
`test_user` / `test_db` を確認または作成し、そのままテストまで実行する
補助スクリプトを使えます。

```powershell
.\scripts\run-db-integration-tests.ps1
```

このスクリプトは、一発で次を行います。

- 対象 PostgreSQL コンテナを特定
- `test_user` ロールを確認または作成
- `test_db` データベースを確認または作成
- `DATABASE_URL` などの環境変数を設定
- `db_integration` マーカー付きテストを実行

既定では、`docker compose` の `db` サービスに対応するコンテナを自動解決します。
明示的に DB を指定したい場合は、コンテナ名または Compose のサービス名を引数で渡してください。

コンテナ名を直接指定する例:

```powershell
.\scripts\run-db-integration-tests.ps1 -DbContainerName osskk_postgres_unified
```

Compose のサービス名から解決させる例:

```powershell
.\scripts\run-db-integration-tests.ps1 -DbServiceName db
```

必要に応じて引数で上書きできます。

```powershell
.\scripts\run-db-integration-tests.ps1 `
  -DbContainerName osskk_postgres_db `
  -AdminUser koiki_user `
  -TestDbName test_db `
  -TestDbUser test_user `
  -TestDbPassword test_pass `
  -EnvFile .env.ci
```

## Scope

- `components/koiki_ref_app/tests/integration/app/api/test_auth_api.py`
- `tests/integration/services/test_auth_service_db.py`
- `tests/integration/services/test_login_security_service_db.py`
- `tests/integration/services/test_user_service_db.py`

## Note

これらのテストは live PostgreSQL と ORM / transaction / API wiring をまとめて検証するため、
失敗時はアプリ実装だけでなく fixture や DB 初期化手順も合わせて確認してください。
