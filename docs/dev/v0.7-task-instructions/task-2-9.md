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

## 次タスク

- [Task 2-10](./task-2-10.md)
