# Task 2-8: ローカル開発導線と helper script の `uv` 化

## 目的

開発者向けの日常手順と補助スクリプトを `uv sync` / `uv run` 基準へ切り替える。

## 推奨ブランチ

- `topic/uv-dev-docs`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-3](./task-2-3.md)
- [Task 2-7](./task-2-7.md)

## 事前条件

- [Task 2-7](./task-2-7.md) が完了している
- `uv.lock` が生成済みである

## 確認観点

- README と setup docs が `uv` を標準経路として説明しているか
- `scripts/` と `ops/` の主要コマンドが `uv run` 前提に揃っているか
- Poetry を残す例外箇所が明示されているか
- 実コード構成と docs 上のパスが一致しているか

## 実施手順

1. README、`docs/dev/local_setup.md`、`docs/dev/test-guide.md` の Poetry 記述を洗い出す
2. 標準経路を `uv sync` / `uv run` ベースへ更新する
3. `scripts/` と `ops/` の Poetry 前提コマンドを `uv run` ベースへ読み替える
4. `poetry build` など当面残す経路があれば、例外として明記する
5. docs 上の path、import、coverage target が現構成と一致しているか見直す

## 成果物

- 更新済み README / local setup / test guide
- 更新済み helper script / ops script

## 検証

- 新規開発者向け手順が `uv` だけで説明できる
- helper script の主要導線に Poetry 前提が残っていない
- docs と実コマンドが一致している

## 完了条件

- ローカル作業の標準経路が Poetry から `uv` に切り替わっている

## 実施結果

Task:

- Task 2-8: ローカル開発導線と helper script の `uv` 化

変更内容:

- README のローカルテスト手順を `uv sync` / `uv run pytest` に更新した
- `docs/dev/local_setup.md` を `uv` 標準手順へ更新した
  - `uv sync`
  - `uv sync --group test`
  - `uv sync --group security`
  - `uv sync --locked`
  - `uv run uvicorn app.main:app --reload`
  - `uv run uvicorn koiki_ref_app.asgi:app --reload`
  - `uv run pytest`
- `docs/dev/setup.md` に `uv` ベースの最小セットアップ手順を追加した
- `docs/dev/test-guide.md` に `uv run pytest` ベースのテスト手順を追加した
- `docs/dev/db-integration-testing.md` の DB integration 実行例を `uv run pytest` に更新した
- `scripts/run-db-integration-tests.ps1` の pytest 実行を `uv run pytest` に更新した
- 日常開発の標準 path として `koiki_ref_app.asgi:app` を明示し、`app.main:app` は互換導線として整理した

Poetry 例外:

- local setup / test guide / README / DB integration helper の主要導線には Poetry 前提を残していない
- 配布物確認は `uv run --with build python -m build components/libkoiki` として記載し、Poetry build を標準経路から外した
- 履歴・計画文書内の Poetry 記述は、移行経緯を説明する文脈として残る

検証結果:

- README、`docs/dev/setup.md`、`docs/dev/local_setup.md`、`docs/dev/test-guide.md`、`docs/dev/db-integration-testing.md`、`scripts/run-db-integration-tests.ps1` に Poetry コマンドが残っていないことを確認した
- 同じ対象ファイルで `uv sync` / `uv run` の標準導線が確認できる
- docs 上の主要 import path は現構成に合わせた
  - `koiki_ref_app.asgi:app`
  - `app.main:app`

次タスクへ渡す事項:

- Task 2-9 では `.github/workflows/ci.yml` を `uv sync --locked` / `uv run --locked ...` へ切り替える
- Task 2-10 では実際に `uv sync`、`uv run pytest --collect-only`、import 検証を行う

## 次タスク

- [Task 2-9](./task-2-9.md)
- [Task 2-10](./task-2-10.md)
