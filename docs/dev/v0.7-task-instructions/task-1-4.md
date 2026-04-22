# Task 1-4: app/pyproject.toml の runtime/dev 分離

## 目的

将来の `koiki_ref_app` に向けて、参照アプリの依存責務を明確にする。

## 参照ファイル

- `app/pyproject.toml`
- `pyproject.toml`

## 事前条件

- [Task 1-1](./task-1-1.md) と [Task 1-3](./task-1-3.md) が完了している

## 確認観点

- runtime に本当に必要な依存
- test/dev にのみ必要な依存
- `koiki_ref_app` に引き継ぐべき依存
- root と重複している依存

## 実施手順

1. `app/pyproject.toml` の依存を分類する
2. test 専用依存を抽出する
3. app 固有 runtime dependency を抽出する
4. 将来の `koiki_ref_app` に引き継ぐ dependency モデルを決める
5. runtime と dev/test の境界を記録する

## 成果物

- dependency 分類メモ
- `koiki_ref_app` 用の依存方針

## 検証

- `pytest` などが runtime に居続ける理由を説明できない状態が解消されている
- 参照アプリ package の責務として妥当な依存集合が見えている

## 完了条件

- app 側の依存責務が Task 2-2 以降に引き渡せる

## 次タスク

- [Task 1-5](./task-1-5.md)
