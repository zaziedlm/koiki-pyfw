# Python 3.13 / Docker / env 整理 作業記録

## 目的

このブランチ `topic/python3-13-fitting` では、v0.7 系のローカル開発と Docker コンテナ開発を進めるため、次の整理を行った。

- ローカル PC 開発環境の Python を 3.13.13 に寄せる。
- Docker backend image の Python ベースも 3.13.13 系へ揃える。
- v0.6 系ブランチの Docker Desktop リソースと混同しないよう、v0.7 用の Compose リソース名を分離する。
- Docker / AWS / production を見据え、`.env*` ファイルの役割を整理する。

この記録は、まだ Docker 実ビルドを行っていない段階での判断経緯と残作業を残すためのもの。

## Python バージョン判断

当初は `.python-version-sample` に Windows 向け `3.11.7` が記載されていたが、開発局面で v0.7 系を進めるため Python 3.13 系を検討した。

確認したこと:

- `pyproject.toml` の `requires-python` は `>=3.11.7,<4.0`。
- `uv python list 3.13` では `cpython-3.13.13-windows-x86_64-none` が利用可能。
- `uv.lock` には重要なネイティブ依存の Python 3.13 wheel が含まれている。
  - `asyncpg`
  - `xmlsec`
  - `psycopg2-binary`
  - `lxml`
  - `cryptography`
- `asyncpg` については `pyproject.toml` コメント上も Python 3.13 support を意識した更新が入っている。

判断:

- ローカル PC 開発環境は Python `3.13.13` を採用する。
- `requires-python` は互換範囲の宣言であるため、この段階では `>=3.11.7,<4.0` のまま維持する。
- Python classifier には 3.12 / 3.13 を追加し、現実の対応範囲を補足する。

## Docker ベースイメージ判断

Dockerfile の backend base image は次の方針にした。

```dockerfile
python:3.13.13-slim-bookworm
```

理由:

- `python:3.13-slim` は 3.13 系の最新パッチへ追従する可変タグで、将来 `3.13.14` 以降が取り込まれる可能性がある。
- `python:3.13.13-slim` は Python patch version は固定されるが、slim の Debian 系が暗黙になりやすい。
- `python:3.13.13-slim-bookworm` なら Python patch version と Debian family を同時に明示できる。
- 今回の論点は Python 3.13 対応であり、Debian `bookworm` から `trixie` への OS 更新は別タスクとして切り出せる。

今後 `3.13.14` などへ上げる場合は、次のように更新単位を分ける。

1. ローカル `uv` で `3.13.14` を確認。
2. CI の `python-version` を更新。
3. Dockerfile を `3.13.14-slim-bookworm` に更新。
4. Debian family 更新は別 PR / 別タスクにする。

## Docker Desktop リソース名の分離

この PC では v0.6 系ブランチの Docker 作業も生きているため、v0.7 系の Compose リソースが混同されないようにした。

対象:

- `container_name`
- Compose project `name`
- named volume の実体名
- network 名は Compose project 名から自然に分離される

変更方針:

- 通常 compose は `koiki_v07_*`
- unified compose は `koiki_v07_unified_*`
- ポート番号は変更しない
  - 同質のコンテナアプリを同時起動しない前提のため
  - 3000 / 8000 / 5432 / 8090 / 9000 は維持

例:

- `koiki_v07_backend`
- `koiki_v07_frontend`
- `koiki_v07_postgres`
- `koiki_v07_keycloak`
- `koiki_v07_unified_postgres_data`
- `koiki_v07_unified_keycloak_data`

## env ファイル整理

env ファイルは、実体ファイルとテンプレートの境界が曖昧だったため、役割を明確化した。

詳細な一覧は `docs/dev/env-files.md` に移した。

大枠:

| ファイル | 用途 |
|---|---|
| `.env.example` | root `.env` のテンプレート。local Docker / dev / optimized 用 |
| `.env.production.example` | root `.env.production` のテンプレート。backend production / AWS 向け |
| `.env.ci` | CI 用の安全な固定値 |
| `.env.saml.example` | SAML 設定の追加テンプレート |
| `.env.test.example` | 任意の file-based local test env テンプレート |
| `frontend/.env.docker` | local Docker frontend 用の具体値 |
| `frontend/.env.local.example` | `frontend/.env.local` のテンプレート |
| `frontend/.env.production.example` | `frontend/.env.production` のテンプレート |

`.env.test` は現行 CI / scripts から直接参照されていなかったため、実体 env に見える名前をやめ、`.env.test.example` に改名した。

## Backend と frontend の env 差分

backend には `frontend/.env.docker` 相当の `.env.docker` を新設していない。

理由:

- backend は root `.env` が local Docker runtime 用も兼ねている。
- `.env.example` には `db` や `keycloak` など Compose service name 前提の値が含まれている。
- したがって root 側は `.env.example -> .env` が local Docker の標準経路になっている。

frontend は Next.js の都合で次の値が分かれる。

- ブラウザに公開される `NEXT_PUBLIC_*`
- server-side / BFF から backend へ接続する `BACKEND_API_URL`
- build 時に焼き込まれる値

そのため frontend では `.env.docker` と `.env.production.example` を分けた。

## Production / AWS 向けの考え方

local Docker Compose の production profile を使う場合:

```powershell
Copy-Item .env.production.example .env.production
Copy-Item frontend\.env.production.example frontend\.env.production
```

frontend production image をビルドする場合は、build arg も合わせる。

```powershell
$env:ENV_FILE = ".env.production"
$env:FRONTEND_ENV_FILE = "./frontend/.env.production"
$env:FRONTEND_BUILD_ENV_FILE = ".env.production"
docker compose -f docker-compose.unified.yml --profile prod build
```

AWS / ECS では `.env.production` を image に焼き込まず、Task Definition の environment / secrets、Secrets Manager、Parameter Store で注入する想定。

## 検証済み

このセッションでは Docker 実ビルドは未実行。

実施済み:

- `uv sync --locked --dry-run --python 3.13.13`
- `docker compose ... config`
  - `docker-compose.yml`
  - `docker-compose.yml` + `docker-compose.dev.yml`
  - `docker-compose.unified.yml --profile dev`
  - `docker-compose.unified.yml --profile prod`
  - `docker-compose.unified.yml --profile prod-external`
- `git diff --check`
- `git check-ignore` による env 実体 / template の追跡確認

未実施:

- backend Docker image build
- frontend Docker image build
- unified dev / prod / prod-external の実起動
- AWS/ECS task definition への反映

## コミット分割方針

このブランチでは、作業の意味が混ざらないようにコミットを分ける。

### 1. Python 3.13 対応

対象:

- `.github/workflows/ci.yml`
- `.python-version-sample`
- `Dockerfile`
- `Dockerfile.unified`
- `pyproject.toml`
- `components/libkoiki/pyproject.toml`
- `docs/dev/local_setup.md`
- `docs/security/SECURITY_AUDIT_COMMANDS.md`

意図:

- local / CI / backend Docker の Python を 3.13.13 方針へ揃える。

### 2. Docker/env 整理

対象:

- `.env.example`
- `.env.production.example`
- `.env.test.example`
- `.env.test` の削除
- `.gitignore`
- `DOCKER_SETUP.md`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.unified.yml`
- `frontend/.gitignore`
- `frontend/.env.production.example`
- `frontend/Dockerfile`
- `frontend/Dockerfile.unified`
- `start-docker.ps1`
- `start-docker.sh`
- `docs/dev/env-files.md`

意図:

- v0.7 用 Docker リソース名を分離する。
- backend/frontend/env の役割を明確化する。
- production / AWS 向けテンプレートを追加する。

### 3. セッション作業記録

対象:

- `docs/dev/python3-13-env-docker-session-notes.ja.md`

意図:

- このセッションの判断経緯、未実施事項、次回作業の前提を残す。

## 次回作業候補

1. 3コミットに分けて commit する。
2. `.env` / `.env.production` / `frontend/.env.production` をローカルに作成する。
3. `docker compose ... build` を profile ごとに実行する。
4. build 後、`docker compose ... up` で smoke check を行う。
5. AWS/ECS 用の env / secrets 設計へ進む。
