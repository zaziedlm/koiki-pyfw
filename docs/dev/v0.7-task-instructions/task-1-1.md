# Task 1-1: 既存 pyproject.toml 群の責務棚卸し

## 目的

root、`libkoiki`、`app` に分散したメタデータの重複と責務混線を見える化する。

## 参照ファイル

- `pyproject.toml`
- `libkoiki/pyproject.toml`
- `app/pyproject.toml`

## 事前条件

- Stage 0 が完了している

## 観点

- runtime dependency
- dev/test dependency
- optional dependency
- build system
- tool 設定
- workspace 的責務か package 的責務か

## 実施手順

1. 3 つの `pyproject.toml` を横並びで読む
2. dependency の重複を一覧化する
3. runtime と dev/test が混ざっている箇所を拾う
4. root に置くべきでない package-specific 設定を拾う
5. 各ファイルの責務を 1 行で言えるように整理する

## 推奨成果物

- 比較表
  - ファイル
  - 役割
  - 問題点
  - 将来のあるべき形

## 検証

- 重複依存が一覧化されている
- 「なぜこの依存がここにあるのか」が説明できない項目が残っていない

## 完了条件

- Task 1-2 から 1-5 の判断材料が揃っている

## 実施結果

Task:

- Task 1-1: 既存 `pyproject.toml` 群の責務棚卸し

変更内容:

- root `pyproject.toml`、`libkoiki/pyproject.toml`、`app/pyproject.toml` の役割と依存構成を比較した
- 3ファイルの責務を次のように整理した
  - root `pyproject.toml`
    - 現状は workspace 的に使われているが、`[project]` にアプリ全体相当の runtime dependency を大量に持っており、配布物と workspace の責務が混在している
  - `libkoiki/pyproject.toml`
    - 再利用ライブラリの package 定義に近いが、Poetry 向けの重複設定と dev/test group が併存している
  - `app/pyproject.toml`
    - 参照アプリ package の雛形としては弱く、runtime dependency に `pytest` と `pytest-asyncio` が入っている
- 主な依存重複を次のように整理した
  - root と `libkoiki` で大部分の framework runtime dependency が重複
    - `fastapi`
    - `uvicorn`
    - `sqlalchemy[asyncio]`
    - `asyncpg`
    - `alembic`
    - `pydantic`
    - `pydantic-settings`
    - `PyJWT[crypto]`
    - `passlib[bcrypt]`
    - `httpx`
    - `structlog`
    - `redis`
    - `slowapi`
    - `tzdata`
- root 固有依存として、現行アプリ側に寄っているものを確認した
  - `psycopg2-binary`
  - `aiosqlite`
  - `email-validator`
  - `bcrypt`
  - `python3-saml`
  - `xmlsec`
  - `python-multipart`
  - `prometheus-fastapi-instrumentator`
  - `anyio`
  - `limits`
  - `libkoiki`
- optional / dev/test の混在を次のように確認した
  - root は `[project.optional-dependencies]` と `[tool.poetry.group.*]` の両方に dev/test/security を重複保持
  - `libkoiki` も `[project.optional-dependencies]` と `[tool.poetry.group.*]` が並存
  - `app` には optional dependency や dev/test group がなく、runtime と test の分離が未実施
- build system の不統一を確認した
  - root: `poetry-core`
  - `libkoiki`: `poetry-core`
  - `app`: `setuptools`

未解決事項:

- root `pyproject.toml` を最終的に PEP 621 の workspace メタにどこまで残すかは Task 1-3 で判断が必要
- `libkoiki` の Poetry 設定をどこまで残すかは Task 1-2 / 1-5 と連動して判断が必要
- `app` を将来 `koiki_ref_app` としてどう package 化するかは Task 1-4 で具体化が必要

検証結果:

- 3つの `pyproject.toml` すべてについて、役割を 1 文で説明できる状態になった
- dependency の重複、runtime/dev 混在、build system の不統一を一覧として説明できる
- Stage 1 の後続タスクで何を決めるべきかが明確になった

次タスクへ渡す事項:

- Task 1-2 では `libkoiki/setup.py` を廃止しても `libkoiki/pyproject.toml` へ一本化できるかを確認する
- Task 1-3 では root `pyproject.toml` から package 的責務をどこまで外すかを判断する
- Task 1-4 では `app/pyproject.toml` から `pytest` を runtime 依存から外す前提で整理する
- Task 1-5 では root にだけ存在する app 寄り依存を `libkoiki` に残すべきかを精査する

## 次タスク

- [Task 1-2](./task-1-2.md)
