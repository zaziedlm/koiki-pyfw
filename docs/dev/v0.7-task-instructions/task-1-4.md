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

## 実施結果

Task:

- Task 1-4: `app/pyproject.toml` の runtime/dev 分離

変更内容:

- `app/pyproject.toml` の現状を確認し、参照アプリ package としては次の問題があると整理した
  - runtime dependency が `libkoiki`、`pytest`、`pytest-asyncio` の3つしかなく、アプリ本体依存の表現として不十分
  - `pytest` と `pytest-asyncio` が runtime dependency に入っており、test dependency が混在している
  - optional dependency や dev/test group が存在しない
  - build backend が `setuptools` で、root / `libkoiki` 側の `poetry-core` 系と不統一
- runtime に残すべき最小要素を次のように整理した
  - `libkoiki`
  - 将来 `koiki_ref_app` として package 化した際に本当に必要な app 固有 runtime dependency
    - 具体例としては SAML/SSO 統合、設定、監視、multipart 処理など、参照アプリで実際に使うもの
- runtime から外すべきものを次のように整理した
  - `pytest`
  - `pytest-asyncio`
- dev/test 側へ移すべきものを次のように整理した
  - `pytest`
  - `pytest-asyncio`
  - 将来的には `pytest-cov`、`pytest-mock` なども app 側 test group に寄せる候補
- package 名についても、現状の `koiki-app` は一時名であり、最終的には `koiki_ref_app` 側へ引き継ぐ前提が妥当と判断した
- 実運用上の前提を確認した結果、テスト実行や起動は root の Poetry / 将来の workspace 経由で行われており、`app/pyproject.toml` 自体に `pytest` を runtime 依存として残す理由は見当たらなかった

未解決事項:

- `app` 固有 runtime dependency の完全一覧は、Task 1-5 の `libkoiki` 境界整理と合わせて確定する必要がある
- build backend を `setuptools` のまま残すか、将来 `koiki_ref_app` で `pyproject.toml` を再設計するかは Stage 2 以降で判断が必要
- `app/pyproject.toml` をそのまま延命するのではなく、`koiki_ref_app` 向けに新規設計し直す可能性が高い

検証結果:

- `pytest` と `pytest-asyncio` が runtime に居続ける理由を説明できない状態が解消された
- 参照アプリ package の依存は「`libkoiki` + app 固有 runtime」に絞るべきという方向が明確になった
- Stage 2 以降で `app` を `koiki_ref_app` へ置き換える際の依存責務が整理できた

次タスクへ渡す事項:

- Task 1-5 では `libkoiki` に残す依存と app 側へ寄せる依存を確定する
- Stage 2 / Stage 5 の方針として、参照アプリ package は runtime と dev/test を明確に分離した `koiki_ref_app` として再定義する
- 現時点の結論として、`app/pyproject.toml` の `pytest` / `pytest-asyncio` は runtime から除外対象である

## 次タスク

- [Task 1-5](./task-1-5.md)
