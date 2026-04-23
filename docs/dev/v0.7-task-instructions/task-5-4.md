# Task 5-4: `components/libkoiki` 実移設

## 目的

framework code を `components/libkoiki` の target layout へ移し、`src/libkoiki` 形式の component として成立させる。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-task-instructions/task-5-1.md`
- `docs/dev/v0.7-task-instructions/task-5-3.md`
- `components/libkoiki/pyproject.toml`
- `pyproject.toml`
- `tests/conftest.py`

## 事前条件

- [Task 5-3](./task-5-3.md) が完了している

## 確認観点

- `components/libkoiki/src/libkoiki` への実移動
- package discovery の追随
- `libkoiki` unit tests の受け皿
- root test 側の import 解決

## 実施手順

1. `components/libkoiki/src/libkoiki` の target layout を作る
2. framework code を新配置へ移す
3. `libkoiki` / `core` unit tests を `components/libkoiki/tests/unit/` へ移す
4. `pyproject.toml` と test import path を新構成へ追随させる
5. `import libkoiki` の最低限の動作を確認する

## 成果物

- `components/libkoiki` の実体
- package / test path 更新

## 検証

- `import libkoiki` が新構成で成功する
- framework unit tests の受け皿が新構成で成立している

## 完了条件

- Task 5-5 で `koiki_ref_app` 側の実移設へ進める

## 実施結果

Task:

- Task 5-4: `components/libkoiki` 実移設

変更内容:

- `components/libkoiki` を新設し、framework code を `src/libkoiki` 形式へ実移動した
  - `components/libkoiki/src/libkoiki/`
    - `api/`
    - `core/`
    - `db/`
    - `events/`
    - `models/`
    - `repositories/`
    - `schemas/`
    - `services/`
    - `tasks/`
    - `utils/`
    - `__init__.py`
  - component 直下へ
    - `AGENTS.md`
    - `CLAUDE.md`
    - `README.md`
    - `pyproject.toml`
    を移した
- `libkoiki` に紐づく unit tests も新構成へ移した
  - `tests/unit/libkoiki/` → `components/libkoiki/tests/unit/libkoiki/`
  - `tests/unit/core/` → `components/libkoiki/tests/unit/core/`
- `components/libkoiki/tests/conftest.py` を追加し、新しい `src` path を pytest 実行時に読めるようにした
- `components/libkoiki/pyproject.toml` の Poetry package discovery を `src` layout 対応へ更新した
  - `packages = [{include = "libkoiki", from = "src"}]`
- root `pyproject.toml` も最小限追随させた
  - local dependency path
    - `libkoiki = {path = "components/libkoiki", develop = true}`
  - pytest `testpaths`
    - `components/libkoiki/tests` を追加
- root `tests/conftest.py` も更新し、app 側テストが新しい `components/libkoiki/src` を優先して import できるようにした
  - `LIBKOIKI_SRC` を `sys.path` の先頭へ追加
  - repo root はその次に追加
- 移動時に巻き込まれた `components/libkoiki` 配下の `__pycache__` は除去した
- root `libkoiki/` には legacy artifact が残る状態になった
  - `.venv/`
  - `libkoiki.egg-info/`
  - `poetry.lock`
  - `setup.py`
  - これらは Stage 1 方針上は最終的に除去対象だが、本タスクでは runtime/package 成立を優先して残した

未解決事項:

- root `libkoiki/` に残っている legacy artifact をどのタスクで除去するかは整理が必要
- CI、Docker、compose、docs、`.github/instructions` の `libkoiki/` filesystem path はまだ未追随
- integration tests の `libkoiki` 帰属分はまだ root `tests/` 側に残っている

検証結果:

- `python -c "..."` で `components/libkoiki/src` を先頭に追加した状態で `import libkoiki` は成功し、`components/libkoiki/src/libkoiki/__init__.py` が読み込まれることを確認した
- 続けて `import libkoiki.core.logging` も試行したが、path 解決ではなく依存未導入により `ModuleNotFoundError: No module named 'structlog'` で停止した
- したがって新構成の import path 自体は通っているが、runtime import の完全確認には依存同期が必要
- `python -m pytest components/libkoiki/tests/unit/core/test_logging_sanitizer.py -q` は試行したが、ローカル Python 環境に `pytest` が入っておらず `No module named pytest` で失敗した
- したがって import 成立は確認済みだが、framework unit test の実行確認は未完了で、後続の依存同期後に再確認が必要

次タスクへ渡す事項:

- Task 5-5 では `koiki_ref_app` の実移設時に、`libkoiki` 参照先が `components/libkoiki` になった前提で package path を更新する
- Task 5-6 以降では CI / Docker / docs / instructions の filesystem path を `components/libkoiki` 前提に直す
- `pytest` 実行確認は依存同期可能な環境で再実施する

## 次タスク

- [Task 5-5](./task-5-5.md)
