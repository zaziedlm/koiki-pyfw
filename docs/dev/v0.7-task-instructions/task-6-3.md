# Task 6-3: Dockerfile 更新設計

## 目的

Docker の更新を 1 回で終わらせるため、install path / COPY path / startup module / bind mount path を新構造へ読み替えた設計を確定する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-5.md`
- `Dockerfile`
- `Dockerfile.unified`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.unified.yml`

## 事前条件

- [Task 6-2](./task-6-2.md) が完了している

## 確認観点

- backend source の COPY path
- Alembic の COPY / mount path
- startup module
- dev bind mount path
- Stage 6 実更新で一括置換する対象一覧

## 実施手順

1. `Dockerfile` / `Dockerfile.unified` の COPY 対象と CMD を確認する
2. `docker-compose*.yml` の command と bind mount を確認する
3. 新構造での正式 path を決める
4. 一時互換で維持するものと、Task 6-4 で一括置換するものを分ける
5. 未追随箇所を整理する

## 成果物

- Docker 更新設計メモ

## 検証

- Compose 変更に必要な入力が揃っている

## 完了条件

- Task 6-4 で Dockerfile / Compose を実更新できる

## 実施結果

Task:

- Task 6-3: Dockerfile 更新設計

変更内容:

- 現行 Docker / Compose の旧構造前提を整理した
  - `COPY ./app ./app`
  - `COPY ./libkoiki ./libkoiki`
  - `COPY ./alembic ./alembic`
  - `COPY ./alembic.ini ./`
  - `uvicorn app.main:app`
  - `./app:/app/app`
  - `./libkoiki:/app/libkoiki`
  - `./alembic:/app/alembic`
- 新構造での読み替え方針を確定した
  - framework source:
    - `components/libkoiki/src/libkoiki`
  - reference app source:
    - `components/koiki_ref_app/src/koiki_ref_app`
  - Alembic:
    - `components/koiki_ref_app/alembic`
    - `components/koiki_ref_app/alembic.ini`
  - startup module:
    - Stage 6 更新時点では互換性維持を優先し、`app.main:app` を継続使用してよい
    - ただし COPY / mount は `components/koiki_ref_app` 実体を基準に更新する
- 実更新の単位を分けた
  - `Dockerfile`
  - `Dockerfile.unified`
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `docker-compose.unified.yml`

未解決事項:

- dependency manager はまだ Poetry 前提なので、Docker の `uv` 化は今回対象外
- `app.main:app` を `koiki_ref_app.asgi:app` へ切り替える最終タイミングは Stage 7 寄りで再判断余地がある
- `docker-entrypoint.sh` の中に旧 Alembic path 前提が残っていないかは Task 6-4 で要確認

検証結果:

- `Dockerfile` と `Dockerfile.unified` の旧 COPY path / startup module を特定した
- `docker-compose.dev.yml` と `docker-compose.unified.yml` の bind mount 置換対象を特定した
- `components/koiki_ref_app/alembic.ini` の `script_location` は component root 基準で成立しており、Docker 側はこの配置に合わせればよいことを確認した
- したがって Task 6-4 で Dockerfile / Compose を一括更新するための入力は揃っている

次タスクへ渡す事項:

- Task 6-4 では Dockerfile / Compose の COPY path、bind mount、Alembic path を新構造へ一括更新する
- `app.main:app` は当面互換として残しつつ、コンテナ内 source path は `components/koiki_ref_app` 実体へ切り替える

## 次タスク

- [Task 6-4](./task-6-4.md)
