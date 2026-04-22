# Task 1-3: root pyproject.toml の workspace 化方針確定

## 目的

root `pyproject.toml` を「配布物」ではなく「workspace 設定」の主体として再定義する。

## 参照ファイル

- `pyproject.toml`
- `libkoiki/pyproject.toml`
- `app/pyproject.toml`

## 事前条件

- [Task 1-1](./task-1-1.md) が完了している

## 確認観点

- root に残す依存
- root から外す依存
- root に残す tool 設定
- 将来の `uv workspace` との整合

## 実施手順

1. root `pyproject.toml` にある依存と tool 設定を分けて見る
2. workspace 管理に必要なものを抽出する
3. package 固有依存が root に混ざっていないか確認する
4. root の責務を 1 文で定義する
5. 将来の `components/` 配置でも成立する形か確認する

## 成果物

- root `pyproject.toml` の責務定義
- root に残す項目一覧
- root から移す項目一覧

## 検証

- root が package 本体ではなく workspace だと説明できる
- `app` 固有依存、`libkoiki` 固有依存が root に残りすぎていない

## 完了条件

- Stage 2 で `uv` workspace 化へ進める

## 次タスク

- [Task 1-4](./task-1-4.md)
