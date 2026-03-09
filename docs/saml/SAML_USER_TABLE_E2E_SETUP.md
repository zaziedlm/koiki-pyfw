# SAML E2E Setup (`user` table backend)

この手順は、`user_sso` テーブルを使わずに `user` テーブル連携 (`SSO_LINK_BACKEND=user_table`) で
SAMLログインE2Eを行うための検証手順です。

## 前提

- Docker / Docker Compose が利用可能
- ルートに `.env.saml.example` が存在
- SAML IdP は `docker/keycloak/realm-saml.json` を利用（同梱済み）

## 1. 自動セットアップ（推奨）

PowerShell:

```powershell
./scripts/setup-saml-user-table-e2e.ps1
```

Bash:

```bash
bash ./scripts/setup-saml-user-table-e2e.sh
```

このスクリプトで以下を実行します。

1. `SSO_LINK_BACKEND=user_table` を `.env` に設定
2. `docker compose down -v --remove-orphans`（ボリューム初期化）
3. `db/keycloak/app/frontend` 起動
4. `app` コンテナ起動時に実行された migration の結果として `alembic_version` を確認
5. 暫定 `"user"` テーブル作成（`scripts/sql/create_user_table_for_sso.sql`）

## 2. 手動セットアップ（必要な場合）

1. `.env` に `SSO_LINK_BACKEND=user_table` を設定
2. コンテナを初期化

```bash
docker compose down -v --remove-orphans
docker compose up -d --build db keycloak app frontend
```

3. マイグレーション確認

`app` コンテナの entrypoint が起動時に `alembic upgrade head` を実行します。  
手動で再度 `alembic upgrade head` を叩かず、結果だけ確認します。

```bash
docker compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT version_num FROM alembic_version;"
```

4. 暫定 `user` テーブル作成

```bash
docker compose exec -T db psql -U koiki_user -d koiki_todo_db < scripts/sql/create_user_table_for_sso.sql
```

## 3. 画面E2E確認

1. ブラウザで `http://localhost:3000/auth/login` を開く
2. SAMLログインを開始
3. Keycloak ログイン画面でテストユーザーを使用

- `saml-user / Passw0rd!`
- `saml-admin / AdminPass123!`
- `saml-test / TestPass123!`

4. コールバック後、ダッシュボード表示と認証成立を確認

## 4. 確認ポイント

- バックエンドログで `Using custom user-table repository backend` が出る
- `user` テーブルの `user_sso_provider`, `user_sso_subject`, `updated_at` が更新される
- 既存の `users` テーブル認証トークン発行フローは継続して利用される

## 4.1. 確認観点

この手順で確認する観点は以下です。

1. 初回 SAML ログイン
- `users` テーブルにフレームワークユーザーが新規作成される
- `user` テーブルに 1 行だけ新規作成される
- 固定値は以下のとおり入る

```text
role_id=5
created_by=sso-system
updated_by=sso-system
```

2. 同一ユーザーでの 2 回目 SAML ログイン
- `user` テーブルの行数は `1` のまま増えない
- `created_at` は初回ログイン時刻のまま変わらない
- `updated_at` は 2 回目ログイン時刻に更新される
- `updated_by=sso-system` が維持される
- アプリログ上でも `INSERT INTO "user"` ではなく `UPDATE "user"` が実行される

## 5. 後片付け

```bash
docker compose down
```

ボリュームも破棄する場合:

```bash
docker compose down -v
```

## トラブルシュート

### `user` テーブルだけ作成され、既存テーブルが無い

想定原因:

- `.env` が SAML設定のみで、DB接続設定 (`DATABASE_URL`, `POSTGRES_*`) が不足
- migration失敗を見逃して後続SQLだけ実行

対処:

1. 最新スクリプトを使用して再実行（DB設定補完 + `alembic_version` 検証あり）
2. 途中失敗時は次のログを確認

```bash
docker compose logs app --tail=200
docker compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT version_num FROM alembic_version;"
```
