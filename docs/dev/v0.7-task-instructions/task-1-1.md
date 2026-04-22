# Task 1-1: 既存 pyproject.toml 群の責務棚卸し

## 目的

root、`libkoiki`、`app` に分散したメタデータの重複と責務混線を見える化する。

## 参照ファイル

- `pyproject.toml`
- `libkoiki/pyproject.toml`
- `app/pyproject.toml`

## 事前条件

- Stage 0 が完了している

## 観点

- runtime dependency
- dev/test dependency
- optional dependency
- build system
- tool 設定
- workspace 的責務か package 的責務か

## 実施手順

1. 3 つの `pyproject.toml` を横並びで読む
2. dependency の重複を一覧化する
3. runtime と dev/test が混ざっている箇所を拾う
4. root に置くべきでない package-specific 設定を拾う
5. 各ファイルの責務を 1 行で言えるように整理する

## 推奨成果物

- 比較表
  - ファイル
  - 役割
  - 問題点
  - 将来のあるべき形

## 検証

- 重複依存が一覧化されている
- 「なぜこの依存がここにあるのか」が説明できない項目が残っていない

## 完了条件

- Task 1-2 から 1-5 の判断材料が揃っている

## 次タスク

- [Task 1-2](./task-1-2.md)
