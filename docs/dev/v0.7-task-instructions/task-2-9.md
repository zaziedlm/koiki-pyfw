# Task 2-9: CI workflow の `uv` 化

## 目的

GitHub Actions を `uv sync --locked` / `uv run --locked ...` 前提へ切り替え、Poetry 依存の CI を解消する。

## 推奨ブランチ

- `topic/uv-ci-migration`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-4](./task-2-4.md)
- [Task 2-7](./task-2-7.md)

## 事前条件

- [Task 2-7](./task-2-7.md) が完了している
- `uv.lock` を CI で参照できる状態である

## 確認観点

- workflow に Poetry install / config step が残っていないか
- cache key が `uv.lock` 基準に切り替わっているか
- test / coverage 実行が `uv run --locked` へ統一されているか
- ローカル標準コマンドとの乖離が小さいか

## 実施手順

1. `.github/workflows/ci.yml` の Poetry 前提 step を洗い出す
2. `uv` のセットアップと cache 方針へ置き換える
3. install を `uv sync --locked` に置き換える
4. test / coverage / tree 表示などを `uv run --locked ...` / `uv tree` に読み替える
5. branch trigger と path 前提が現構成と整合するか再確認する

## 成果物

- 更新済み `.github/workflows/ci.yml`
- `uv` ベース CI への切替記録

## 検証

- workflow に Poetry 固有 step が残っていない
- CI が `uv.lock` を基準に依存解決する構成になっている
- test と coverage の標準経路が `uv` に揃っている

## 完了条件

- Task 2-10 で local / CI 横断検証に進める

## 実施結果

Task:

- Task 2-9: CI workflow の `uv` 化

変更内容:

- `.github/workflows/ci.yml` から Poetry 前提 step を削除した
  - Poetry install
  - Poetry config
  - `.venv` / `poetry.lock` cache
  - `poetry check --lock`
  - `poetry install`
  - `poetry run pytest`
  - `poetry show --tree`
- `astral-sh/setup-uv` による `uv` セットアップを追加した
- cache dependency を `uv.lock` に切り替えた
- lockfile 整合確認を `uv lock --check` に変更した
- dependency install を `uv sync --locked --group dev --group test` に変更した
- test / coverage 実行を `uv run --locked pytest ...` に変更した
- dependency tree 表示を `uv tree --locked` に変更した
- 既存のテスト分割は維持した
  - `libkoiki` unit / agent guidance
  - `koiki_ref_app` / integration services

検証結果:

- `.github/workflows/ci.yml` に Poetry 固有 step が残っていないことを確認した
- workflow が `uv.lock` を cache dependency として参照していることを確認した
- install / test / coverage の標準経路が `uv` に揃った
- branch trigger は現行の `main` / `dev/v0.7` / `support/0.6` / `topic/*` / `feature/*` のまま維持した

未解決事項:

- GitHub Actions 上での実行結果はまだ未確認
- Task 2-10 で local の `uv sync` / collect / import 検証を行う

次タスクへ渡す事項:

- Task 2-10 では local で `uv sync`、`uv run pytest --collect-only`、`uv run python -c "import libkoiki, koiki_ref_app"` を確認する
- CI の実ラン結果は push / PR 後に確認する

## 次タスク

- [Task 2-10](./task-2-10.md)
