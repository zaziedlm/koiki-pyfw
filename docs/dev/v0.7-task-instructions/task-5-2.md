# Task 5-2: `components/koiki_ref_app` 移設準備

## 目的

参照アプリを `components/koiki_ref_app` へ移す前に、Stage 3 / Stage 4 で確定した app factory、ORM bootstrap、starter domain、互換起動導線を前提に、配置と責務を確定する。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-3-2.md`
- `docs/dev/v0.7-task-instructions/task-3-3.md`
- `docs/dev/v0.7-task-instructions/task-3-5.md`
- `docs/dev/v0.7-task-instructions/task-4-1.md`
- `docs/dev/v0.7-task-instructions/task-4-2.md`
- `docs/dev/v0.7-task-instructions/task-4-5.md`
- `app/pyproject.toml`
- `app/main.py`
- `main.py`
- `alembic.ini`

## 事前条件

- [Task 5-1](./task-5-1.md) が完了している

## 確認観点

- `bootstrap/`
- `asgi.py`
- `app_factory.py`
- app 固有 modules の配置
- Alembic と app 側 tests の扱い
- `app.main:app` 互換維持の置き場所

## 実施手順

1. 現在の `app/` 配下構造を確認する
2. `koiki_ref_app` に残すものと `libkoiki` / `apps/` へ出るものを再確認する
3. `src/koiki_ref_app/` 配下の target layout を定義する
4. Alembic、ASGI path、compat wrapper の配置方針を定義する
5. 実移設時の修正対象と未確定点を整理する

## 成果物

- `components/koiki_ref_app` 構成案
- app 側移設前チェックメモ

## 検証

- `koiki_ref_app` 配下の構成案が確定している
- Stage 5 後半で path move に入るための修正対象が説明できる

## 完了条件

- Task 5-3 で test 配置移設準備へ進める

## 実施結果

Task:

- Task 5-2: `components/koiki_ref_app` 移設準備

変更内容:

- 現在の `app/` 配下を確認し、参照アプリとして移す対象を整理した
  - app 固有 API
    - `api/v1/router.py`
    - `api/v1/endpoints/sso_auth.py`
    - `api/v1/endpoints/saml_auth.py`
    - `api/v1/endpoints/business_clock.py`
  - app 固有 config
    - `core/sso_config.py`
    - `core/saml_config.py`
  - app 固有 DB / ORM
    - `db/base.py`
    - `models/`
    - `repositories/`
    - `schemas/`
    - `services/`
  - app package metadata
    - `pyproject.toml`
    - `main.py`
  - component 直下に残す候補
    - `README.md`
    - `alembic.ini`
    - `alembic/`
    - component 専用 tests
- Stage 3 / 4 の結論を踏まえ、`koiki_ref_app` の target layout を次のように定義した
  - `components/koiki_ref_app/pyproject.toml`
  - `components/koiki_ref_app/README.md`
  - `components/koiki_ref_app/alembic.ini`
  - `components/koiki_ref_app/alembic/`
  - `components/koiki_ref_app/src/koiki_ref_app/asgi.py`
  - `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`
  - `components/koiki_ref_app/src/koiki_ref_app/bootstrap/`
  - `components/koiki_ref_app/src/koiki_ref_app/api/`
  - `components/koiki_ref_app/src/koiki_ref_app/core/`
  - `components/koiki_ref_app/src/koiki_ref_app/db/`
  - `components/koiki_ref_app/src/koiki_ref_app/models/`
  - `components/koiki_ref_app/src/koiki_ref_app/repositories/`
  - `components/koiki_ref_app/src/koiki_ref_app/schemas/`
  - `components/koiki_ref_app/src/koiki_ref_app/services/`
- `app_factory.py` / `asgi.py` / `bootstrap/` の役割も次のように固定した
  - `app_factory.py`
    - `create_app()` の source of truth
    - FastAPI instance 作成
    - framework helper 呼び出し順制御
    - app-specific bootstrap 呼び出し
  - `asgi.py`
    - `app = create_app()` を置く正式 ASGI entrypoint
  - `bootstrap/`
    - app-specific bootstrap helper を分離配置
    - 例:
      - ORM bootstrap
      - router registration
      - SSO / SAML bootstrap
      - business feature bootstrap
- Stage 3 の ORM bootstrap 方針とも接続した
  - `bootstrap/orm.py` 相当を持たせ
    - `load_app_models()`
    - `register_model_extensions()`
    - `bootstrap_orm()`
    を置くのが自然と整理した
  - `app/models/__init__.py` の副作用は最終的に薄くする前提
- app 固有 modules の配置方針も整理した
  - SSO / SAML は `koiki_ref_app` に残す
  - `business_clock` は starter domain として `koiki_ref_app` に残す前提
  - `todo` は Stage 3 判断どおり `koiki_ref_app` 側へ受ける
  - customer 固有 code は `apps/` に出す
- Alembic の扱いも確定した
  - 現在の root `alembic/` と `alembic.ini` は app 合成済み schema に紐づくため `koiki_ref_app` 側へ移す
  - `components/koiki_ref_app/alembic/`
  - `components/koiki_ref_app/alembic.ini`
  - `alembic/env.py` は Stage 3 の ORM bootstrap 明示化設計を反映する更新対象
- 互換起動導線の配置も整理した
  - 正式な将来 ASGI path は `koiki_ref_app.asgi:app`
  - ただし Stage 5 / 6 では `app.main:app` 互換を維持する
  - そのため現行 `app/main.py` は、移設後もしばらく薄い wrapper として残す前提
  - root `main.py` も Stage 7 までは互換 wrapper 候補
- path / import の基本方針も確認した
  - Python package 名は最終的に `koiki_ref_app` に変わる
  - したがって `from app...` / `import app...` は実移設後に更新対象
  - `app.main:app` 互換維持期間は wrapper で吸収する
- 実移設時の主な修正対象を次のように分類した
  - packaging
    - `app/pyproject.toml` を `koiki_ref_app` package 前提に再設計
  - runtime path
    - `main.py`
    - `Dockerfile`
    - `docker-compose*.yml`
    - docs の `uvicorn app.main:app`
  - migration
    - root `alembic/`
    - `alembic.ini`
    - `alembic/env.py`
  - tests
    - `tests/unit/app/`
    - `tests/conftest.py`
    - `from app.main import app` 依存箇所
  - app imports
    - `from app.core...`
    - `from app.services...`
    - `from app.repositories...`
    - `from app.schemas...`
    - `from app.models...`
- 生成物と除外対象も確認した
  - `app/__pycache__/` は移設対象ではない
  - `app/AGENTS.md` と `app/CLAUDE.md` は component 直下 guidance として残すか後続判断
- Task 5-2 時点の構成説明を次の一文で固定した
  - `koiki_ref_app` は `libkoiki` を土台に、app factory、ORM bootstrap、starter domain、Alembic を持つ backend starter component である

未解決事項:

- `business_clock` を starter domain に正式維持するかは、Stage 5 実移設時に最小 starter 観点で再確認してよい
- `app/AGENTS.md` と `app/CLAUDE.md` を `components/koiki_ref_app/` にどう引き継ぐかは後続判断が必要
- `koiki_ref_app` の package import 変更に伴う `from app...` 一括更新は、実移設タスクで順番を誤ると破断しやすいため慎重に進める必要がある

検証結果:

- `koiki_ref_app` 配下の target layout と `bootstrap/` / `app_factory.py` / `asgi.py` の責務を説明できる状態になった
- Alembic と互換起動導線を app 側 component の責務として扱う前提が固まった
- Task 5-3 以降で test 配置と実移設へ入るための修正対象一覧が揃った

次タスクへ渡す事項:

- Task 5-3 では、root `tests/` と component tests の境界を `libkoiki` / `koiki_ref_app` 双方に跨って整理する
- Task 5-4 / 5-5 の実移設では、wrapper を残しつつ package path を段階的に切り替える
- Stage 6 では Docker / Compose / docs / CI の `app.main:app` や root Alembic path を一括更新する

## 次タスク

- [Task 5-3](./task-5-3.md)
