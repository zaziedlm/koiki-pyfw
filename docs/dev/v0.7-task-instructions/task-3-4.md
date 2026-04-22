# Task 3-4: `todo` 境界の再配置判断

## 目的

`todo` を framework に残すか、参照アプリ側へ移すかを確定する。

## 参照ファイル

- `libkoiki/api/v1/endpoints/todos.py`
- `libkoiki/models/todo.py`
- `libkoiki/services/todo_service.py`
- `tests/integration/app/api/test_todos_api.py`

## 事前条件

- [Task 3-3](./task-3-3.md) が完了している

## 確認観点

- code と test の現在位置
- sample / reference としての妥当な配置
- Stage 5 での移設対象

## 実施手順

1. `todo` 関連 code の配置を確認する
2. `todo` 関連 test の配置を確認する
3. framework capability と sample/reference app の境界で評価する
4. 残す案 / 移す案を比較する
5. 推奨配置と移設対象一覧を記録する

## 成果物

- `todo` 配置判断メモ
- 移設対象一覧

## 検証

- `todo` の責務位置が曖昧なまま残っていない
- Stage 5 までに移動方針が確定している

## 完了条件

- Task 3-5 以降で router / 起動互換を判断できる

## 実施結果

Task:

- Task 3-4: `todo` 境界の再配置判断

変更内容:

- `todo` 関連 code の現在位置を次のように整理した
  - API
    - `libkoiki/api/v1/endpoints/todos.py`
    - `libkoiki/api/v1/router.py` で `/todos` を標準 include
  - Model
    - `libkoiki/models/todo.py`
    - `libkoiki/models/user.py` 側に `todos` relation
  - Repository / Service / Schema
    - `libkoiki/repositories/todo_repository.py`
    - `libkoiki/services/todo_service.py`
    - `libkoiki/schemas/todo.py`
  - Dependency wiring
    - `libkoiki/api/dependencies.py` に `TodoServiceDep`
- `todo` 関連 test の現在位置も整理した
  - integration
    - `tests/integration/app/api/test_todos_api.py`
      - 現状は実質スタブに近い
  - e2e
    - `tests/e2e/test_pyjwt_e2e.py`
      - `/todos` を通した認証付き動作確認を含む
  - unit / logging
    - `tests/unit/libkoiki/test_input_logging.py`
      - `TodoCreate` / `TodoUpdate`
      - `libkoiki.services.todo_service`
      - `libkoiki.api.v1.endpoints.todos`
- 配置評価を framework capability と sample/reference の2観点で整理した
  - framework capability として reusable な部分
    - CRUD service / repository / schema の作り方自体
    - 認証、transactional、rate limiter、logging との統合パターン
  - sample/reference として project-specific な部分
    - `todos` という具体ドメイン
    - `libkoiki.api.v1.router` に標準ルーターとして同梱されていること
    - `ToDos Sample` というタグ名
    - E2E / integration で参照アプリ的に扱われていること
- 残す案と移す案を比較した
  - framework に残す案
    - 利点
      - demo と smoke test の入口としてすぐ使える
    - 問題
      - reusable framework と sample domain が混ざる
      - `libkoiki.api.v1.router` が sample endpoint を標準露出する
      - `todo` が framework の責務に見えてしまう
  - 参照アプリへ移す案
    - 利点
      - `libkoiki` を auth / config / persistence / bootstrap の共通基盤へ寄せられる
      - `todo` を starter / reference app のサンプル機能として位置づけ直せる
      - Stage 4 のテンプレートモデルと整合する
    - 問題
      - 一部 unit / e2e test の import path 更新が必要
      - framework router からの除去に伴う互換対応が必要
- 推奨判断を次のように確定した
  - `todo` は framework 本体ではなく、参照アプリ / starter template に寄せる
  - したがって Stage 5 の target は `components/koiki_ref_app` 側が妥当
- 移設対象一覧も次のように整理した
  - API
    - `libkoiki/api/v1/endpoints/todos.py`
    - `libkoiki/api/v1/router.py` の `/todos` include
  - Model / Schema / Repository / Service
    - `libkoiki/models/todo.py`
    - `libkoiki/schemas/todo.py`
    - `libkoiki/repositories/todo_repository.py`
    - `libkoiki/services/todo_service.py`
    - `libkoiki/api/dependencies.py` の `TodoServiceDep`
  - 関連 relation
    - `libkoiki/models/user.py` の `todos`
  - test
    - `tests/integration/app/api/test_todos_api.py`
    - `tests/e2e/test_pyjwt_e2e.py` の `/todos` 使用箇所
    - `tests/unit/libkoiki/test_input_logging.py` の todo 関連部分
- 移設後の位置づけも整理した
  - `todo` は `koiki_ref_app` に置く sample / starter domain
  - framework 側には、必要なら generic CRUD / auth / transaction / logging の extension point のみ残す
  - `libkoiki.api.v1.router` からは `todos` 標準 include を外す方向
- 互換期間の考え方も記録した
  - Stage 3 / 4 では方針のみ確定
  - 実際の import path と router 変更は Stage 5 の components 移設に合わせる
  - 必要なら一時的な wrapper / re-export を持つ

未解決事項:

- `TodoService` 等を完全移設するのか、framework 側に generic base service を残して参照アプリ側で具象化するのかは実装時に判断が必要
- E2E テストで `/todos` を smoke endpoint として使い続けるか、別の reference endpoint に置き換えるかは後続判断
- `UserModel.todos` relation を framework 側から除去する場合の互換影響は別途精査が必要

検証結果:

- `todo` の責務位置を framework ではなく reference / starter app として説明できる状態になった
- Stage 5 までに移動方針が確定し、曖昧さは解消された
- router、model、service、test のどこを移すかの対象一覧も揃った

次タスクへ渡す事項:

- Task 3-5 では、`app.main` 互換 wrapper 設計時に `todos` の互換露出をどう扱うかも意識する
- Stage 4 / Stage 5 では、`todo` を `koiki_ref_app` の starter domain として扱う前提で README / template scope を定義する
- 実移設時には `libkoiki.api.v1.router` から `todos` を外す差分を明示管理する

## 次タスク

- [Task 3-5](./task-3-5.md)
