# Task 5-5: `components/koiki_ref_app` 実移設

## 目的

参照アプリを `components/koiki_ref_app` の target layout へ移し、`koiki_ref_app` package を起点に読み込める状態へ寄せる。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-2.md`
- `docs/dev/v0.7-task-instructions/task-5-3.md`
- `components/koiki_ref_app/pyproject.toml`
- `components/koiki_ref_app/alembic/env.py`
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py`
- `app/main.py`

## 事前条件

- [Task 5-4](./task-5-4.md) が完了している

## 確認観点

- `components/koiki_ref_app/src/koiki_ref_app` への実移動
- `create_app()` と `asgi.py` の導入
- 互換 `app.main:app` の維持
- Alembic の移設

## 実施手順

1. `components/koiki_ref_app` の target layout を作る
2. `app/` 配下の実体を `src/koiki_ref_app/` へ移す
3. `app_factory.py` と `asgi.py` を配置する
4. Alembic を `components/koiki_ref_app/` へ移す
5. 旧 `app` は compatibility wrapper に縮退させる
6. `import koiki_ref_app` と `from app.main import app` の最小確認を行う

## 成果物

- `components/koiki_ref_app` の実体
- 互換 `app` wrapper
- `koiki_ref_app.asgi:app`

## 検証

- `import koiki_ref_app` が新構成で成功する
- `from app.main import app` が path 解決面で新構成を読める

## 完了条件

- Task 5-6 で `apps/` 導入に進める

## 実施結果

Task:

- Task 5-5: `components/koiki_ref_app` 実移設

変更内容:

- `components/koiki_ref_app` を新設し、参照アプリ実体を `src/koiki_ref_app` 形式へ移動した
  - `components/koiki_ref_app/src/koiki_ref_app/`
    - `api/`
    - `core/`
    - `db/`
    - `models/`
    - `repositories/`
    - `schemas/`
    - `services/`
    - `app_factory.py`
    - `asgi.py`
    - `__init__.py`
    - `bootstrap/__init__.py`
- component 直下へ次を移した
  - `AGENTS.md`
  - `CLAUDE.md`
  - `pyproject.toml`
  - `alembic/`
  - `alembic.ini`
- `components/koiki_ref_app/src/koiki_ref_app/app_factory.py` を `create_app()` 起点に整理した
  - `FastAPI` インスタンス生成を `create_app()` に集約
  - app 固有 router は `koiki_ref_app.api.v1.router` から include する構成へ変更
- `components/koiki_ref_app/src/koiki_ref_app/asgi.py` を追加し、正式 ASGI entrypoint を `koiki_ref_app.asgi:app` とした
- 旧 `app/` は compatibility layer として残した
  - `app/__init__.py`
    - `components/koiki_ref_app/src` と `components/libkoiki/src` を `sys.path` に追加
    - `app.*` import が `koiki_ref_app` 実体を引けるよう package path を延長
  - `app/main.py`
    - `from koiki_ref_app.asgi import app` だけを持つ薄い wrapper に置き換え
- `components/koiki_ref_app/alembic/env.py` を新配置に追随させた
  - `koiki_ref_app` と `libkoiki` の `src` path を明示的に `sys.path` へ追加
  - app import を `koiki_ref_app.*` に変更
  - `target_metadata` を `AppBase.metadata` に変更
- root 側も最小限追随させた
  - `tests/conftest.py`
    - `components/koiki_ref_app/src` を `sys.path` に追加
  - `pyproject.toml`
    - coverage source に `koiki_ref_app` を追加
- `components/koiki_ref_app/pyproject.toml` を参照アプリ component 前提に更新した
  - name を `koiki_ref_app` に変更
  - runtime dependency から `pytest` / `pytest-asyncio` を除去
  - `tool.setuptools.packages.find.where = ["src"]` を追加

未解決事項:

- 旧 `app.*` import は compatibility layer で当面動かすが、source 全体の import rename はまだ未完了
- `tests/unit/app` と `tests/integration/app` はまだ root `tests/` 側に残っており、Task 5-7 で物理移設が必要
- Docker / Compose / CI / docs の `app.main:app` / `alembic.ini` path はまだ未追随
- `components/koiki_ref_app/README.md` は未整備

検証結果:

- `python -c "..."` で `components/koiki_ref_app/src` と `components/libkoiki/src` を追加した状態で `import koiki_ref_app` は成功し、`components/koiki_ref_app/src/koiki_ref_app/__init__.py` が読み込まれることを確認した
- `from app.main import app` は path 解決自体は新構成へ切り替わったが、ローカル環境に `fastapi` がないため `ModuleNotFoundError: No module named 'fastapi'` で停止した
- `components/koiki_ref_app/alembic/env.py` の import 実行も試行したが、ローカル環境に `sqlalchemy` がないため `ModuleNotFoundError: No module named 'sqlalchemy'` で停止した
- したがって新構成の path / package 配置は成立しているが、runtime 確認には依存同期が必要

次タスクへ渡す事項:

- Task 5-6 では `apps/` を導入し、`components/` と `apps/` の境界を実ディレクトリで明示する
- Task 5-7 では root `tests/unit/app` / `tests/integration/app` を `components/koiki_ref_app/tests` へ移す
- Stage 6 で Docker / Compose / CI / Alembic path を `components/koiki_ref_app` / `koiki_ref_app.asgi:app` 前提へ更新する

## 次タスク

- [Task 5-6](./task-5-6.md)
