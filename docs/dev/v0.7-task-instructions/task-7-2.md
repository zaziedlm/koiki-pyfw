# Task 7-2: legacy import / shim 除去

## 目的

`components/koiki_ref_app` 実装と test から旧 `app` import 依存を除去し、互換 wrapper に依存しない内部参照へ寄せる。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-7-1.md`
- `components/koiki_ref_app/src/koiki_ref_app/**`
- `components/koiki_ref_app/tests/**`
- `tests/conftest.py`

## 事前条件

- [Task 7-1](./task-7-1.md) が完了している

## 確認観点

- `components/koiki_ref_app` 実装が `from app...` に依存していないか
- `components/koiki_ref_app` test が `from app...` や `patch("app....")` に依存していないか
- root `tests/conftest.py` が `app.main` ではなく `koiki_ref_app.asgi` を参照できるか
- 意図的に残す wrapper と、ここで除去する legacy import が分離できているか

## 実施手順

1. `components/koiki_ref_app/src/koiki_ref_app/**` の `from app...` を `koiki_ref_app...` へ置換する
2. `components/koiki_ref_app/tests/**` の import / patch 文字列を `koiki_ref_app...` へ置換する
3. `tests/conftest.py` の FastAPI app import を `koiki_ref_app.asgi` へ切り替える
4. `rg` で `from app...` / `import app...` / `app.main:app` の残件を確認する
5. wrapper として意図的に残すものだけを未解決へ整理する

## 成果物

- `koiki_ref_app` 実装 / test 群の更新
- legacy import 除去の記録

## 検証

- `components/koiki_ref_app` 実装と test から旧 `app` import が消えている
- `app.main:app` は wrapper として意図的に残す箇所だけに限定されている

## 完了条件

- Task 7-3 で side-effect bootstrap 整理へ進める

## 実施結果

Task:

- Task 7-2: legacy import / shim 除去

変更内容:

- `components/koiki_ref_app/src/koiki_ref_app/**` の旧 `app` import を `koiki_ref_app...` へ置換した
  - `services/sso_service.py`
  - `services/saml_service.py`
  - `services/saml_certificate_manager.py`
  - `services/kkbiz/business_clock_service.py`
  - `repositories/saml_auth_flow_repository.py`
  - `repositories/sso_link_repository_factory.py`
  - `repositories/user_sso_repository.py`
  - `repositories/user_table_sso_repository.py`
  - `repositories/kkbiz/business_clock_repository.py`
  - `api/v1/endpoints/sso_auth.py`
  - `api/v1/endpoints/saml_auth.py`
  - `api/v1/endpoints/business_clock.py`
- `components/koiki_ref_app/tests/**` の import / patch 対象を `koiki_ref_app...` へ置換した
  - `test_sso_service.py`
  - `test_saml_service.py`
  - `test_saml_support_logging.py`
  - `test_saml_auth_flow_repository_logging.py`
  - `test_user_table_sso_repository.py`
  - `test_business_clock_service.py`
- root `tests/conftest.py` の app import を `from koiki_ref_app.asgi import app` へ変更した

未解決事項:

- root `main.py` の `from app.main import app` と `uvicorn.run("app.main:app", ...)` は互換 wrapper として意図的に残している
- `app/__init__.py` と `app/main.py` 自体も、互換導線として未削除
- runtime / test 実行の完全確認は依存同期後に必要

検証結果:

- `rg` により、旧 `app` import は意図的に残した `main.py` / `app` wrapper を除いて解消された
- `components/koiki_ref_app` 実装と test 群は、内部的に `koiki_ref_app...` を正本として参照する状態になった
- したがって Stage 7-3 以降は wrapper 本体と bootstrap 副作用の整理に集中できる

次タスクへ渡す事項:

- Task 7-3 では ORM / bootstrap の副作用依存をさらに明示化する
- wrapper 本体の除去判断は Stage 7 後半で行う

## 次タスク

- [Task 7-3](./task-7-3.md)
