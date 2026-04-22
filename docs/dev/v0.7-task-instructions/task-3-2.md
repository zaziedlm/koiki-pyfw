# Task 3-2: `create_app()` の責務定義

## 目的

新しい app factory の責務範囲を確定し、framework helper と参照アプリ側 bootstrap の境界を明確にする。

## 参照ファイル

- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`
- `docs/dev/v0.7-directory-reorganization-plan.ja.md`
- `docs/dev/v0.7-task-instructions/task-3-1.md`
- `app/main.py`

## 事前条件

- [Task 3-1](./task-3-1.md) が完了している

## 確認観点

- framework 側 helper と app 側 `create_app()` の境界
- `create_app()` の入力
- `create_app()` の戻り値
- 初期化順

## 実施手順

1. Task 3-1 の責務一覧を app factory 観点で再分類する
2. framework helper に落とす責務を抽出する
3. app layer に残す bootstrap を抽出する
4. `create_app()` の入力、戻り値、呼び出し順を定義する
5. 暫定互換 wrapper の要否も整理する

## 成果物

- `create_app()` の責務定義メモ
- framework helper / app bootstrap 分担表

## 検証

- `create_app()` の責務が 1 枚で説明できる
- framework 側と app 側の責務混線がない

## 完了条件

- Task 3-3 で ORM bootstrap と初期化順を詰められる

## 実施結果

Task:

- Task 3-2: `create_app()` の責務定義

変更内容:

- Task 3-1 で整理した `app.main` の責務を、app factory 観点で次の3層に再分類した
  - framework helper
  - app-specific bootstrap
  - composition root としての `create_app()`
- framework helper に置く責務を次のように定義した
  - FastAPI app 共通設定 helper
    - title / version / docs_url / redoc_url / openapi_url の設定
  - 共通 middleware registration helper
    - CORS
    - security headers
    - audit log
    - request context
  - 共通 exception handler registration helper
    - `setup_exception_handlers(app)`
  - monitoring helper
    - `setup_monitoring(app)` の有効化条件を含む
  - Redis / event publisher / limiter bootstrap helper
    - app.state 初期化
    - Redis 接続可否分岐
    - rate limiter 初期化
    - `RateLimitExceeded` handler 登録
  - DB connect / disconnect helper
    - `connect_db()`
    - `disconnect_db()`
- app-specific bootstrap に残す責務を次のように定義した
  - app 固有 router include
    - `app.api.v1.router`
  - app 固有 background task
    - SAML flow cleanup task
  - app 固有 degraded startup policy
    - 必要なら Redis 不使用時の app-specific fallback 振る舞い
  - app 固有 bootstrap 設定
    - 将来の SSO / SAML 初期化、business feature bootstrap
- `create_app()` 本体の責務を次のように定義した
  - FastAPI instance を生成する
  - framework helper と app-specific bootstrap の呼び出し順を制御する
  - lifecycle を束ねる
  - 呼び出し側がそのまま `uvicorn` の import target にできる `FastAPI` を返す
  - 自身はビジネスロジックや SAML 処理の詳細を持たない
- `create_app()` の入力も次のように整理した
  - 必須入力
    - なし
    - 既定では project settings を読む
  - 将来の明示入力候補
    - `settings_override`
    - `enable_monitoring`
    - `include_app_routes`
    - `include_framework_routes`
    - `register_model_extensions`
  - ただし Stage 3 では、引数を増やしすぎず「既定 settings ベース + 必要最小限の override」に留める方針が妥当
- `create_app()` の戻り値は `FastAPI` インスタンスと定義した
  - app state 上に次を持つ前提も併記した
    - `redis`
    - `redis_pool`
    - `event_publisher`
    - `event_handler`
    - `limiter`
- 初期化順も次のように定義した
  1. logging 準備
  2. app instance 生成
  3. middleware / exception handler / monitoring の static registration
  4. router registration
  5. lifespan / startup / shutdown wiring
  6. startup 中で DB / Redis / limiter / app-specific background task を順に初期化
  7. shutdown 中で app-specific task / Redis / DB を逆順で解放
- この順序を採る理由も整理した
  - middleware / exception handler は app instance 作成直後に静的登録できる
  - DB / Redis は起動時 resource なので lifespan 内へ置く
  - app 固有 background task は Redis / DB など共通資源が整った後に起動すべき
- 暫定互換 wrapper の要否も整理した
  - 要
  - 当面は `app/main.py` に
    - `app = create_app()`
    - 既存 `uvicorn app.main:app` を維持
  - これにより Stage 3 中も既存起動導線を壊さない
- 目標モジュール構成の叩き台も定義した
  - framework 側
    - `libkoiki/app_factory.py` または `libkoiki/bootstrap/*.py`
  - app 側
    - `app/app_factory.py`
    - `app/bootstrap/*.py`
    - `app/main.py` は互換 wrapper
- 境界の原則も明文化した
  - framework helper は reusable resource / middleware / lifecycle 補助のみ
  - app-specific bootstrap は SSO / SAML / business feature / app router を持つ
  - `create_app()` は composition root であり、長大な実装本体に戻さない

未解決事項:

- framework helper を `libkoiki/app_factory.py` に集約するか、`libkoiki/bootstrap/` へ分割するかは Task 3-3 以降で調整が必要
- logging 初期化を import 時副作用から外し、`create_app()` の前段または内部で明示化するかは未決定
- framework router と app router の include 順が認可・ドキュメント表示へ与える影響は、後続タスクで確認が必要

検証結果:

- `create_app()` の責務を「FastAPI instance 作成 + lifecycle wiring + helper 呼び出し順制御」として 1 枚で説明できる状態になった
- framework 側と app 側の責務混線を避ける境界が明確になった
- 既存起動導線を壊さないための暫定互換 wrapper も必要と判断できた

次タスクへ渡す事項:

- Task 3-3 では、今回定義した初期化順を前提に ORM bootstrap の発火点を設計する
- Task 3-5 では、`app.main` 互換 wrapper の形を今回の結論に沿って具体化する
- Task 3-4 の `todo` 再配置判断も、framework router / app router の境界整理と連動させる

## 次タスク

- [Task 3-3](./task-3-3.md)
