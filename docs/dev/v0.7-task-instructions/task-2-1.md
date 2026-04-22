# Task 2-1: uv 導入ポリシーの定義

## 目的

Poetry から `uv` へ何を置き換えるかを先に明文化し、移行中の判断ぶれを防ぐ。

## 参照文書

- [v0.7-directory-reorganization-plan.ja.md](../v0.7-directory-reorganization-plan.ja.md)
- [v0.7-directory-reorganization-tasks.ja.md](../v0.7-directory-reorganization-tasks.ja.md)

## 事前条件

- [Task 1-6](./task-1-6.md) が完了している

## 決める内容

- `uv sync` を標準セットアップコマンドにするか
- `uv run` を標準実行コマンドにするか
- `uv.lock` を正規 lockfile にするか
- root workspace と member 管理をどう扱うか

## 実施手順

1. 現在 Poetry が担っている役割を列挙する
2. それぞれを `uv` でどう置き換えるか定義する
3. ローカル開発、CI、将来の `components/` 移動への影響を確認する
4. 「何を `uv` に置換し、何を置換しないか」を文章化する
5. 標準コマンド一覧を作る

## 成果物

- `uv` 導入ポリシーメモ
- 標準コマンド一覧

## 検証

- Poetry と `uv` の責務差分が説明できる
- チームが使う標準コマンドを 1 セットで示せる

## 完了条件

- Task 2-2 以降がこの方針で判断できる

## 次タスク

- [Task 2-2](./task-2-2.md)
