# Task 1-5: libkoiki dependency 境界の整理

## 目的

`libkoiki` に残すべき framework dependency と、参照アプリ側へ寄せるべき依存を切り分ける。

## 参照ファイル

- `libkoiki/pyproject.toml`
- `app/pyproject.toml`
- `docs/agent/boundaries.md`

## 事前条件

- [Task 1-1](./task-1-1.md) が完了している

## 確認観点

- `libkoiki` が再利用フレームワークとして必要とする依存
- app 固有の認証・SSO・SAML 依存
- migration や DB 運用依存の帰属

## 実施手順

1. `libkoiki` の依存を 1 つずつ責務で評価する
2. `app` 寄り依存を抽出する
3. `alembic` の帰属を判断する
4. `python3-saml`、`xmlsec` などの app 寄り依存の扱いを決める
5. `libkoiki` に残す依存の理由を記録する

## 成果物

- `libkoiki` dependency 分類メモ
- 残す依存と移す依存の一覧

## 検証

- 各依存について「別アプリでも必要か」を説明できる
- app 固有依存が framework package に混ざったままになっていない

## 完了条件

- `libkoiki` の再利用責務に沿った依存境界が定義されている

## 次タスク

- [Task 1-6](./task-1-6.md)
