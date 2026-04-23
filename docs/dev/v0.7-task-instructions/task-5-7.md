# Task 5-7: test 実移設

## 目的

テストを component 所有に近づけ、`libkoiki` と `koiki_ref_app` の責務境界に沿った配置へ寄せる。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-3.md`
- `components/koiki_ref_app/tests/conftest.py`
- `components/libkoiki/tests/conftest.py`
- `pyproject.toml`

## 事前条件

- [Task 5-6](./task-5-6.md) が完了している

## 確認観点

- `tests/unit/app` の `koiki_ref_app` 側移設
- `tests/integration/app` の `koiki_ref_app` 側移設
- `koiki_ref_app` 側 fixture 自立
- pytest `testpaths` の追随

## 実施手順

1. `tests/unit/app` を `components/koiki_ref_app/tests/unit/` へ移す
2. `tests/integration/app` を `components/koiki_ref_app/tests/integration/` へ移す
3. `components/koiki_ref_app/tests/conftest.py` を作成する
4. pytest `testpaths` を新構成へ追随させる
5. 新配置が成立していることを確認する

## 成果物

- `components/koiki_ref_app/tests/`
- app 側 test fixture
- pytest path 更新

## 検証

- `components/koiki_ref_app/tests` 配下に app unit/integration tests が存在する
- `tests/unit/app` と `tests/integration/app` が root からなくなる

## 完了条件

- Stage 5 の test 配置変更が反映され、Stage 6 の周辺追随へ進める

## 実施結果

Task:

- Task 5-7: test 実移設

変更内容:

- app 側 unit tests を root `tests/` から `components/koiki_ref_app/tests` へ移した
  - `tests/unit/app/` → `components/koiki_ref_app/tests/unit/app/`
- app 側 integration tests も同様に移した
  - `tests/integration/app/` → `components/koiki_ref_app/tests/integration/app/`
- `components/koiki_ref_app/tests/conftest.py` を追加し、app 側テストが新構成だけで動ける fixture を用意した
  - `components/koiki_ref_app/src`
  - `components/libkoiki/src`
  - repo root
  を `sys.path` へ追加
  - `test_client` は `koiki_ref_app.asgi:app` を読むようにした
- root `pyproject.toml` の pytest `testpaths` に `components/koiki_ref_app/tests` を追加した

未解決事項:

- root `tests/conftest.py` はまだ広い fixture を持っており、shared 最小化は後続整理余地がある
- 実 test 実行確認には `pytest` / `fastapi` / `sqlalchemy` など依存同期が必要

検証結果:

- `components/koiki_ref_app/tests` 配下に app unit/integration tests が存在する
- root `tests/unit/app` と `tests/integration/app` は消えた
- pytest `testpaths` は新配置を含むよう更新済み

次タスクへ渡す事項:

- Task 5-8 では Stage 5 の結果検証として、components/apps/tests の新配置を横断確認する
- Stage 6 で CI / Docker / docs に新しい test path と app path を追随させる

## 次タスク

- [Task 5-8](./task-5-8.md)
