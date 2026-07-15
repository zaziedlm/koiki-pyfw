# vNext DB 再作成 runbook

更新日: 2026-07-15

対象: `20260715001` の単一Alembic baselineを使うKOIKI-FW管理DB

## 1. 適用範囲と重要な前提

- vNextは空のPostgreSQL DBからだけ再現する。旧Alembic headからのupgrade、またはvNextから旧schemaへのdowngradeは提供しない。
- 旧DBを調査する必要がある場合は、`db-schema-pre-vnext-202607` tagと[移行ノート](db-vnext-migration-note.ja.md)を使う。vNext treeへ旧revisionを混在させない。
- `downgrade base`は検証用に空DBへ戻すためだけに使う。本番DBの復旧手段ではない。
- production相当環境で投入するのはreference bootstrap seedだけである。固定パスワードの開発・E2Eユーザーseedは絶対に実行しない。

## 2. 破壊操作前の確認

再作成の対象はDB名と接続先を二重確認する。特にホストから実行する場合、Composeネットワーク用の`db`ではなく`localhost`を使う。

```powershell
# ホスト側で使う接続先の例
$env:DATABASE_URL = "postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db"
$env:POSTGRES_SERVER = "localhost"

# target DBの名前・接続ユーザー・現在のAlembic revisionを確認する
docker compose exec db psql -U koiki_user -d koiki_todo_db -c "SELECT current_database(), current_user;"
docker compose exec db psql -U koiki_user -d koiki_todo_db -c "SELECT version_num FROM alembic_version;"
```

`current_database()`が意図した再作成対象でない場合は、この先を実行しない。

## 3. ローカルDocker Composeでの再作成

以下の例は通常の`docker-compose.yml`と、`koiki_todo_db`を再作成する場合である。DB名、所有者、Compose profileを環境に合わせて置き換える。

```powershell
# 1. DBコンテナを起動し、対象DBの接続を切断する
docker compose up -d db
docker compose exec db psql -U koiki_user -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'koiki_todo_db' AND pid <> pg_backend_pid();"

# 2. ここから破壊的操作
docker compose exec db psql -U koiki_user -d postgres -c "DROP DATABASE koiki_todo_db;"
docker compose exec db psql -U koiki_user -d postgres -c "CREATE DATABASE koiki_todo_db OWNER koiki_user;"

# 3. vNext baselineを適用する（コンテナ内ではDATABASE_URLのhostはdb）
docker compose exec app alembic -c /app/components/koiki_ref_app/alembic.ini upgrade head

# 4. referenceアプリの初期運用データだけを投入する
docker compose exec app python -m koiki_ref_app.bootstrap.reference_seed
```

unified production profileでは`docker compose -f docker-compose.unified.yml --profile prod`を各コマンドの先頭に付け、app serviceを`app-prod`に置き換える。

```powershell
docker compose -f docker-compose.unified.yml --profile prod exec db psql -U koiki_user -d koiki_todo_db -c "SELECT current_database(), current_user;"
docker compose -f docker-compose.unified.yml --profile prod exec app-prod alembic -c /app/components/koiki_ref_app/alembic.ini upgrade head
docker compose -f docker-compose.unified.yml --profile prod exec app-prod python -m koiki_ref_app.bootstrap.reference_seed
```

## 4. 開発・E2E専用seed

reference bootstrap seedはroles、permissions、関連表、`kkbiz_business_clock(id=1)`を冪等に投入するが、ユーザーや固定パスワードは作らない。

開発またはtesting環境で固定パスワードのE2Eユーザーが必要な場合だけ、reference seedの後に実行する。

```powershell
# APP_ENV=development または testing でのみ許可される
docker compose exec app python ops/scripts/setup_security.py
```

production相当の`APP_ENV`ではこのコマンドは拒否される。production / prod-externalでこのseedを許可する設定変更は行わない。

## 5. 再作成後の検証

```powershell
# ホスト側: target DBに対するrevision、head、ORM/schema driftを確認
uv run --locked alembic -c components/koiki_ref_app/alembic.ini current
uv run --locked alembic -c components/koiki_ref_app/alembic.ini heads
uv run --locked alembic -c components/koiki_ref_app/alembic.ini check

# DB側: 管理対象テーブルとreference seed結果を確認
docker compose exec db psql -U koiki_user -d koiki_todo_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
docker compose exec db psql -U koiki_user -d koiki_todo_db -c "SELECT count(*) AS roles FROM koiki_roles; SELECT count(*) AS permissions FROM koiki_permissions; SELECT count(*) AS business_clock_rows FROM kkbiz_business_clock; SELECT count(*) AS users FROM koiki_users;"
```

期待値は、Alembic headが`20260715001`、管理対象テーブルが12、reference bootstrap後のbusiness clockが1行、ユーザーが0行である。開発・E2E seedを意図して追加実行した場合だけ、最後のユーザー件数は0以外となる。

## 6. CI / PostgreSQL統合検証

Docker上のPostgreSQLを用意して、次を実行する。

```powershell
.\scripts\run-db-integration-tests.ps1 -DbContainerName koiki_v07-db-1
```

このスクリプトは`test_db`に通常のDB統合回帰を実行し、`koiki_baseline_contract`に空schemaからのupgrade、catalog契約、`downgrade base`、再upgradeを実行する。両DBと`test_user`はテスト専用であり、運用DB名を引数に渡してはならない。

## 7. 最終状態（DB-10完了時点）

| 項目 | 値 |
| --- | --- |
| Alembic head | `20260715001` |
| revision構成 | `down_revision = None`の単一baseline |
| 管理対象テーブル | 12（`koiki_*`、`kkref_*`、`kkbiz_business_clock`） |
| baseline内容 | DDLのみ |
| production初期データ | reference bootstrap seed（ユーザーなし） |
| DB-08検証 | baseline contract、schema drift、upgrade/downgrade/re-upgrade |
| DB-09検証 | auth/session/token/password reset/permission、Todo、SSO/SAML、business clock、Index catalog |
| 後続 | DB-PERF-01は非ブロッキングの性能再評価 |

Docker entrypointは既存baselineの`upgrade head`だけを行う。migration失敗時にrevisionをautogenerateしないため、schema変更は必ずレビュー済みの新revisionとして明示的に追加する。
