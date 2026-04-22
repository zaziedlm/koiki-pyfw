# Task 2-4: CI の uv 化

## 目的

CI を Poetry 依存から切り離し、`uv` ベースの依存管理とテスト実行へ移行する。

## 参照対象

- `.github/workflows/`
- root `pyproject.toml`
- `uv` 導入ポリシー

## 事前条件

- [Task 2-3](./task-2-3.md) が完了している
- ローカル側の標準 `uv` コマンドが定まっている

## 確認観点

- Poetry 前提の install 手順
- キャッシュ戦略
- test 実行コマンド
- branch trigger との整合

## 実施手順

1. 現在の CI workflow を棚卸しする
2. Poetry を前提にした箇所を抽出する
3. `uv` 版の install / run / test フローを設計する
4. キャッシュ方針の変更要否を判断する
5. ローカル手順との差異を記録する

## 成果物

- CI 置換方針メモ
- `uv` ベースの workflow 設計

## 検証

- CI が `uv` で何をするか説明できる
- ローカルと CI でコマンド体系が大きく乖離していない

## 完了条件

- 実 workflow 変更に着手できる設計材料が揃っている

## 次タスク

- [Task 2-5](./task-2-5.md)
