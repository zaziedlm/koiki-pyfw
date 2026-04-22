# Task 6-4: Dockerfile / Compose 実更新

## 目的

Dockerfile / Compose を新構造へ追随させ、旧 `app` / `libkoiki` / root `alembic` 前提を外す。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-6-3.md`
- `Dockerfile`
- `Dockerfile.unified`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.unified.yml`
- `docker-entrypoint.sh`

## 事前条件

- [Task 6-3](./task-6-3.md) が完了している

## 確認観点

- Docker build 時の COPY path
- dev bind mount path
- Alembic 実行 path
- 互換 `app.main:app` 維持

## 実施手順

1. `Dockerfile` / `Dockerfile.unified` の COPY path を `components/` 前提へ更新する
2. `docker-compose.dev.yml` / `docker-compose.unified.yml` の bind mount を `components/` 前提へ更新する
3. `docker-entrypoint.sh` の Alembic 実行 path を `components/koiki_ref_app` へ更新する
4. 旧 path の残りを確認する

## 成果物

- 更新済み Dockerfile 群
- 更新済み Compose 群
- 更新済み `docker-entrypoint.sh`

## 検証

- Compose 変更に必要な入力が反映されている

## 完了条件

- Task 6-5 で docs / instructions の path 更新へ進める

## 実施結果

Task:

- Task 6-4: Dockerfile / Compose 実更新

変更内容:

- `Dockerfile` を新構造へ追随させた
  - `COPY ./components ./components`
  - `app` wrapper は維持するため `COPY ./app ./app`
  - Alembic versions 作成先を `/app/components/koiki_ref_app/alembic/versions` に変更
- `Dockerfile.unified` も同様に追随させた
  - `COPY ./components ./components`
  - 旧 `./libkoiki` / `./alembic` / `./alembic.ini` の個別 COPY を除去
- `docker-compose.dev.yml` の bind mount を更新した
  - `./app:/app/app`
  - `./components:/app/components`
  - `./ops:/app/ops`
- `docker-compose.unified.yml` の dev profile bind mount も同様に更新した
  - `./app:/app/app`
  - `./components:/app/components`
  - `./ops:/app/ops`
- `docker-entrypoint.sh` の Alembic 実行 path を component 側へ更新した
  - `ALEMBIC_INI=/app/components/koiki_ref_app/alembic.ini`
  - `ALEMBIC_VERSIONS_DIR=/app/components/koiki_ref_app/alembic/versions`
  - `alembic -c "$ALEMBIC_INI" ...`
- startup module は互換維持を優先し、まだ `app.main:app` を継続した

未解決事項:

- `docker-compose.yml` の command は互換 `app.main:app` のままで、`koiki_ref_app.asgi:app` への最終切替は未実施
- `docker-compose.yml` 自体は bind mount を持たないため path 更新は不要だったが、運用文書上の説明はまだ未追随
- 実 build / compose up は未実行のため、コンテナ起動確認は後続で必要

検証結果:

- `Dockerfile` / `Dockerfile.unified` から旧 `./libkoiki` / root `./alembic` COPY は除去された
- dev compose から旧 `./libkoiki` / `./alembic` bind mount は除去され、`./components` bind mount に置き換わった
- `docker-entrypoint.sh` は root `alembic` ではなく `components/koiki_ref_app/alembic.ini` を使う形になった
- したがって Docker / Compose の path 前提は新構造へ追随した

次タスクへ渡す事項:

- Task 6-5 で docs / `.github/instructions` の旧 path 説明を更新する
- Task 6-6 で Stage 6 全体の検証と未解決事項整理を行う

## 次タスク

- [Task 6-5](./task-6-5.md)
