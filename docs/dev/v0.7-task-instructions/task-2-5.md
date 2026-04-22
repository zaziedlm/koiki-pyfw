# Task 2-5: Stage 2 結果検証

## 目的

`uv` 移行の方針と前提が、Stage 3 以降に進める品質へ達しているか確認する。

## 参照タスク

- [Task 2-1](./task-2-1.md)
- [Task 2-2](./task-2-2.md)
- [Task 2-3](./task-2-3.md)
- [Task 2-4](./task-2-4.md)

## 事前条件

- Stage 2 の成果物が揃っている

## 確認観点

- `uv` の標準コマンドが定義されているか
- workspace member 方針が pre/post move 両方で説明できるか
- ローカルと CI が同じ `uv` モデルで整理されているか
- Stage 5 で `uv` 周りを全面再設計しなくて済むか

## 実施手順

1. Stage 2 の成果物を横断レビューする
2. ローカル、CI、workspace 設計の一貫性を確認する
3. 未解決事項を列挙する
4. 未解決事項が Stage 3 着手を妨げるか判定する
5. 問題なければ Stage 3 着手可と記録する

## 成果物

- Stage 2 レビュー結果
- Stage 3 着手可否判定

## 検証

- `uv sync`、`uv run`、`uv.lock` が標準経路として説明できる
- Stage 5 で設定破綻しない見通しがある

## 完了条件

- app factory と bootstrap 抽出へ進んでよいと判断できる

## 次タスク

- Stage 3 / Task 3-1
