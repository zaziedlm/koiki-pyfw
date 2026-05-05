# Task 3-6: Stage 3 結果検証

## 目的

app factory 導入方針が directory move 前に十分安定しているか確認する。

## 参照ファイル

- `docs/dev/v0.7-task-instructions/task-3-1.md`
- `docs/dev/v0.7-task-instructions/task-3-2.md`
- `docs/dev/v0.7-task-instructions/task-3-3.md`
- `docs/dev/v0.7-task-instructions/task-3-4.md`
- `docs/dev/v0.7-task-instructions/task-3-5.md`

## 事前条件

- Stage 3 の成果物が揃っている

## 確認観点

- `create_app()` 設計
- bootstrap 順
- 互換導線

## 実施手順

1. Stage 3 の成果物を横断レビューする
2. `create_app()` と ORM bootstrap の整合を確認する
3. `todo` 再配置判断と router 境界の整合を確認する
4. 互換起動導線が Stage 5 の移動まで耐えられるか判定する
5. Stage 4 / 5 着手可否を記録する

## 成果物

- Stage 3 レビュー結果
- Stage 4 / 5 着手可否判定

## 検証

- Stage 5 の path 移動に耐えられる構成になっている
- `create_app()`、ORM bootstrap、互換 wrapper の順序が矛盾していない

## 完了条件

- Stage 4 に進んでよいと判断できる

## 実施結果

Task:

- Task 3-6: Stage 3 結果検証

変更内容:

- Task 3-1 から Task 3-5 の成果物を横断レビューし、Stage 3 の設計到達点を次のように整理した
  - `app.main` の責務が startup / shutdown / middleware / router / background task に分解済み
  - `create_app()` は composition root として定義済み
  - ORM bootstrap は `load_app_models()` / `register_model_extensions()` / `bootstrap_orm()` として明示化方針が定義済み
  - `todo` は framework ではなく reference / starter app 側へ寄せる方針が確定済み
  - `app.main:app` を維持する暫定互換 wrapper 方針が定義済み
- `create_app()` と ORM bootstrap の整合も次のように確認した
  - `create_app()` は app instance 生成前後の初期化順を制御する前提
  - ORM bootstrap は router include や DB 利用より前に呼ぶ前提
  - この2つは矛盾せず、`create_app()` の早い段階で `bootstrap_orm()` を呼ぶ構成で整合する
- `todo` 再配置判断と router 境界の整合も確認した
  - `todo` を `koiki_ref_app` 側へ移す前提により、framework router は auth / users / security など reusable 領域へ絞れる
  - app router と framework router の役割分離を Stage 5 でより明確にできる
  - `create_app()` 設計とも衝突しない
- 互換起動導線が Stage 5 の移動まで耐えられるかも次のように判定した
  - `app.main:app` を暫定 import target として維持するため、ローカル、Docker、tests、docs は Stage 3 中は壊れない
  - root `main.py` も維持するので、補助的な起動導線も残せる
  - Stage 6 で ASGI path を一括更新する方針と整合する
- Stage 3 の統合モデルを次のようにまとめた
  - source of truth
    - `app.app_factory.create_app`
  - early bootstrap
    - logging
    - ORM bootstrap
  - static registration
    - middleware
    - exception handlers
    - monitoring
    - router
  - runtime lifecycle
    - DB
    - Redis
    - limiter
    - app-specific background task
  - compatibility layer
    - `app.main:app`
    - root `main.py`
- Stage 4 / 5 の観点から見た blocker の有無も判定した
  - blocker なし
  - ただし Stage 3 は設計完了であり、実装差分はまだ残る
- blocker ではない未解決事項を次のように一覧化した
  - logging 初期化を import 時副作用から外す具体案
  - framework helper を `libkoiki/app_factory.py` か `libkoiki/bootstrap/` のどちらへ置くか
  - `configure_mappers()` を明示呼び出しするか
  - `TodoService` 等を generic base 化するか、そのまま reference app へ移すか
  - root `main.py` の削除タイミング
- 上記未解決事項についても評価した
  - いずれも Stage 4 / 5 着手を止める blocker ではない
  - 主に実装・配置の詳細設計であり、Stage 3 の構造方針自体は安定している
- Stage 4 / 5 着手可否を次のように記録した
  - Stage 4 着手可
  - Stage 5 着手可
  - 前提:
    - `create_app()` を source of truth にする
    - `todo` は `koiki_ref_app` 側へ寄せる
    - `app.main:app` 互換は Stage 6 までは維持する

未解決事項:

- Stage 3 は実装前の設計固定なので、実コード移行時には一部順序の再調整が必要になる可能性がある
- `app.db.base.Base` と `libkoiki.db.base.Base` の整理は Stage 5 までに再確認したい
- Stage 4 でテンプレート責務を定義した後、`todo` の scope をより厳密に見直す余地はある

検証結果:

- Stage 5 の path 移動に耐えられる構成として説明できる状態になった
- `create_app()`、ORM bootstrap、互換 wrapper の順序は矛盾していない
- Stage 4 のテンプレートモデル定義へ進んでよいと判断できた

次タスクへ渡す事項:

- Stage 4 / Task 4-1 では、`koiki_ref_app` に残す責務を今回の `todo` 判断と app factory 方針に沿って定義する
- 実装フェーズでは、`app.main` を薄い wrapper へ縮退させることを中心に進める
- Stage 5 では、member path 更新だけで済むように app factory / bootstrap module の配置を意識する

## 次タスク

- Stage 4 / Task 4-1
