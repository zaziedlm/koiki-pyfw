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

## 次タスク

- [Task 2-9](./task-2-9.md)
- [Task 2-10](./task-2-10.md)
