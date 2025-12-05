# KOIKI Framework Docker セットアップガイド（統一構成版）

unified 構成（profiles: `dev` / `optimized` / `prod` / `prod-external`）を正とした運用ガイドです。旧 `docker-compose.production*.yml` などのレガシー構成は廃止しました。

## 前提
- Docker / Docker Compose がインストール済み
- PowerShell から実行する想定（Linux/macOS では `start-docker.sh` を読み替え）
- 初回のみ `.env` と `frontend/.env.local` をテンプレから作成
  ```powershell
  Copy-Item .env.example .env
  Copy-Item frontend\.env.local.example frontend\.env.local
  ```

## 利用する compose / Dockerfile
- Compose: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.unified.yml`
- Dockerfile: ルート `Dockerfile`, `Dockerfile.unified` / frontend `Dockerfile`, `Dockerfile.unified`

## 起動スクリプト概要
`start-docker.ps1` の主なコマンド:
- 通常構成: `up` / `build` / `down`（`docker-compose.yml`）
- 開発オーバーレイ: `dev` / `build-dev` / `down-dev`（`docker-compose.yml` + `docker-compose.dev.yml`）
- unified 構成:
  - `unified-dev`（フォアグラウンド）
  - `unified-optimized`, `unified-prod`, `unified-prod-external`（デタッチ）
  - それぞれに `-build` / `-down` あり

## プロファイル別の使い分け
- `dev`: ホットリロード開発用（volume mount）
- `optimized`: 軽量化＋キャッシュ効かせた検証用（本番相当の依存でビルド）
- `prod`: 内蔵 Postgres ＋ Keycloak を含む本番相当
- `prod-external`: 外部マネージド DB / 外部 IdP を想定（db/keycloak コンテナなし）

### 外部 DB / IdP 利用時（prod-external）
`.env.production` に以下を設定してください（例示）。
```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@mydb.example.com:5432/DBNAME
SSO_ISSUER_URL=https://idp.example.com
SSO_AUTHORIZATION_ENDPOINT=https://idp.example.com/auth
SSO_TOKEN_ENDPOINT=https://idp.example.com/token
SSO_JWKS_URI=https://idp.example.com/jwks
```
必要に応じて証明書を `docker/certs` に置き、`NODE_EXTRA_CA_CERTS` などで参照します。

## よく使う手順（PowerShell）

### 初回セットアップ
```powershell
# 環境変数ファイル
Copy-Item .env.example .env
Copy-Item frontend\.env.local.example frontend\.env.local

# 必要なら .env.production も作成
Copy-Item .env.example .env.production
```

### 開発
```powershell
.\start-docker.ps1 unified-dev          # ホットリロードで起動（フォアグラウンド）
# 停止: Ctrl+C または別ターミナルで
.\start-docker.ps1 unified-dev-down
```

### 本番相当（内蔵 DB/Keycloak）
```powershell
.\start-docker.ps1 unified-prod-build   # 変更があればビルド
.\start-docker.ps1 unified-prod         # デタッチで起動
.\start-docker.ps1 unified-prod-down    # 停止
```

### 本番相当（外部 DB/IdP）
```powershell
# .env.production に外部DB/IdP設定を入れる
.\start-docker.ps1 unified-prod-external-build
.\start-docker.ps1 unified-prod-external
.\start-docker.ps1 unified-prod-external-down
```

### ログ
```powershell
.\start-docker.ps1 logs           # 旧来の compose 用
.\start-docker.ps1 unified-logs   # unified 全サービス
```

## 環境ファイルの扱い
- `.env`: dev / optimized 用（`ENV_FILE=.env` としてセットされる）
- `.env.production`: prod / prod-external 用（`ENV_FILE=.env.production` としてセットされる）
- frontend の Docker 環境は `frontend/.env.docker` を使用（自動コピーはしないので注意）
- ローカル開発のみ `frontend/.env.local`

## 不要になったファイル
- `docker-compose.production*.yml`、`docker-compose.optimized.yml`、`docker-compose.base.yml`、`docker-compose.unified.dev.yml` は廃止（削除予定）
- それに対応する `Dockerfile.production` / `Dockerfile.optimized`（ルート・frontend）も廃止対象

## トラブルシューティング
- 404 で `_next/static` が取れない: Next.js のビルド成果物配置を確認（unified Frontend は修正済み）。再ビルドして `unified-optimized`/`prod` を再起動。
- 停止・再起動の基本: `unified-*-down` → `unified-*-build`（必要なら）→ `unified-*`
- ポート衝突: `3000/8000/5432/8090` が空いているか確認

## リファレンス（コマンド早見）
```powershell
# 開発
.\start-docker.ps1 unified-dev
.\start-docker.ps1 unified-dev-down

# 検証（軽量ビルド）
.\start-docker.ps1 unified-optimized-build
.\start-docker.ps1 unified-optimized
.\start-docker.ps1 unified-optimized-down

# 本番相当（内蔵 DB/IdP）
.\start-docker.ps1 unified-prod-build
.\start-docker.ps1 unified-prod
.\start-docker.ps1 unified-prod-down

# 本番相当（外部 DB/IdP）
.\start-docker.ps1 unified-prod-external-build
.\start-docker.ps1 unified-prod-external
.\start-docker.ps1 unified-prod-external-down

# ログ
.\start-docker.ps1 unified-logs
```
