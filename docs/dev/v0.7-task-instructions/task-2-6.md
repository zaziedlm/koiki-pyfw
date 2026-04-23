# Task 2-6: root workspace の `uv` メタデータ実装

## 目的

root `pyproject.toml` を Poetry 前提から `uv` workspace 前提へ切り替え、以後の `uv.lock` 生成と CI 切替の土台を作る。

## 推奨ブランチ

- `topic/uv-workspace-activation`

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)
- [Task 2-1](./task-2-1.md)
- [Task 2-2](./task-2-2.md)

## 事前条件

- [Task 2-5](./task-2-5.md) が完了している
- `components/libkoiki` と `components/koiki_ref_app` の現構成が最新状態である

## 確認観点

- root が workspace 実行起点として説明できるか
- `dependency-groups` と `tool.uv.workspace` の責務が衝突していないか
- local package 参照が `tool.uv.sources` に統一できているか
- Poetry 固有設定をどこまで残すかが明示されているか

## 実施手順

1. 現在の root `pyproject.toml` に残っている Poetry 固有設定を棚卸しする
2. `dependency-groups` に移す対象と、`project.optional-dependencies` に残す対象を切り分ける
3. `tool.uv.workspace.members` を現構成に合わせて定義する
4. `tool.uv.sources` で `libkoiki` などの local package 参照を定義する
5. Poetry 固有 group や重複 dependency 記述の整理方針を反映する
6. 変更後の `pyproject.toml` を読み、workspace 起点の説明が通るか確認する

## 成果物

- 更新済み root `pyproject.toml`
- `uv` workspace metadata の反映記録

## 検証

- root `pyproject.toml` に `dependency-groups`、`tool.uv.workspace`、`tool.uv.sources` が入っている
- workspace member が `components/libkoiki` と `components/koiki_ref_app` に一致している
- `uv` 実行起点を root として一貫して説明できる

## 完了条件

- Task 2-7 で `uv lock` を生成できる前提が整っている

## 次タスク

- [Task 2-7](./task-2-7.md)
