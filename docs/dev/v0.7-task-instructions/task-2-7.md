# Task 2-7: `uv.lock` 生成と lockfile 切替

## 目的

`uv.lock` を正規 lockfile として成立させ、Poetry lockfile 依存から切り替える。

## 推奨ブランチ

- `topic/uv-lock-adoption`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-6](./task-2-6.md)

## 事前条件

- [Task 2-6](./task-2-6.md) が完了している
- root workspace metadata が `uv` 用に反映されている

## 確認観点

- `uv lock` が依存解決に成功するか
- component 間参照が lock 解決を妨げていないか
- `poetry.lock` の扱いが曖昧になっていないか
- lockfile 切替順序が docs と一致しているか

## 実施手順

1. `uv lock` 実行前に、依存競合の可能性がある箇所を確認する
2. `uv lock` を実行し、`uv.lock` を生成する
3. lock 解決に失敗した場合は dependency 定義を修正し、再実行する
4. 生成された `uv.lock` が root workspace と component 依存を反映しているか確認する
5. `poetry.lock` を残すか削除するかの切替タイミングを決める
6. lockfile の正本を `uv.lock` とする方針を docs に反映する

## 成果物

- `uv.lock`
- lockfile 切替方針メモ

## 検証

- `uv.lock` が生成されている
- lock 解決に失敗する未解決 dependency conflict が残っていない
- `poetry.lock` の扱いが文書上で説明できる

## 完了条件

- Task 2-8 と Task 2-9 が `uv.lock` を前提に進められる

## 次タスク

- [Task 2-8](./task-2-8.md)
- [Task 2-9](./task-2-9.md)
