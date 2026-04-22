# Task 1-3: root pyproject.toml の workspace 化方針確定

## 目的

root `pyproject.toml` を「配布物」ではなく「workspace 設定」の主体として再定義する。

## 参照ファイル

- `pyproject.toml`
- `libkoiki/pyproject.toml`
- `app/pyproject.toml`

## 事前条件

- [Task 1-1](./task-1-1.md) が完了している

## 確認観点

- root に残す依存
- root から外す依存
- root に残す tool 設定
- 将来の `uv workspace` との整合

## 実施手順

1. root `pyproject.toml` にある依存と tool 設定を分けて見る
2. workspace 管理に必要なものを抽出する
3. package 固有依存が root に混ざっていないか確認する
4. root の責務を 1 文で定義する
5. 将来の `components/` 配置でも成立する形か確認する

## 成果物

- root `pyproject.toml` の責務定義
- root に残す項目一覧
- root から移す項目一覧

## 検証

- root が package 本体ではなく workspace だと説明できる
- `app` 固有依存、`libkoiki` 固有依存が root に残りすぎていない

## 完了条件

- Stage 2 で `uv` workspace 化へ進める

## 実施結果

Task:

- Task 1-3: root `pyproject.toml` の workspace 化方針確定

変更内容:

- root `pyproject.toml` の内容を、次の3区分で整理した
  - runtime dependency
  - optional / dev / security dependency
  - tool / build / workspace 設定
- 現状の root `pyproject.toml` は、`tool.poetry.package-mode = false` により workspace 的に扱っている一方で、`[project]` にアプリ全体相当の runtime dependency を持っており、責務が混在していると判断した
- root に残すべきものを次のように整理した
  - workspace レベルの Python version 制約
  - ルート全体の build / tool 設定
    - `tool.pytest.ini_options`
    - `tool.coverage.*`
    - 将来の `tool.uv.workspace`
  - ルート全体で共有する最小限の開発補助設定
- root から外すべきものを次のように整理した
  - package 本体の runtime dependency 群
  - `app` 固有依存
    - `python3-saml`
    - `xmlsec`
    - `prometheus-fastapi-instrumentator`
    - `python-multipart`
    - `psycopg2-binary`
    - `aiosqlite`
    - `email-validator`
    - `bcrypt`
  - framework package 固有依存
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
    - `anyio`
    - `limits`
    - `libkoiki`
- optional dependency / Poetry group の重複も root から減らすべきと判断した
  - dev/test/security の依存定義は、最終的に `uv` group または workspace 向け最小定義へ寄せる
  - Poetry 固有 group に依存した構成は縮小対象
- root の責務を次の 1 文で定義した
  - root `pyproject.toml` は、配布対象 package ではなく、複数 component と全体ツール設定を束ねる workspace メタデータである

未解決事項:

- `tool.pytest.ini_options` と `tool.coverage.*` を root に残すか、component 分割後に再配置するかは Stage 5 / 6 でもう一度見直しが必要
- `dev` / `test` / `security` group を root にどこまで残すかは、Task 2-1 の `uv` 導入ポリシーと連動して判断が必要
- root `[project]` セクション自体をどこまで縮小するかは、Stage 2 の `uv workspace` 設計時に具体化が必要

検証結果:

- root が package 本体ではなく workspace だと 1 文で説明できる状態になった
- root に残すものと外すものを役割ベースで区分できた
- `app` 固有依存、`libkoiki` 固有依存が root に残りすぎている現状が明確になった

次タスクへ渡す事項:

- Task 1-4 では `app/pyproject.toml` の runtime / dev 分離を進める
- Task 1-5 では `libkoiki` に残すべき依存境界を確定する
- Task 2-1 では root `pyproject.toml` を workspace メタへ寄せる前提で `uv` 導入ポリシーを定義する
- Stage 2 の編集方針としては、「root は workspace、runtime dependency は各 component package」へ寄せる

## 次タスク

- [Task 1-4](./task-1-4.md)
