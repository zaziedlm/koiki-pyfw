# Task 3-1: 現行起動シーケンスの棚卸し

## 目的

`app.main` が現在担っている責務を分解し、app factory 抽出の対象を明確にする。

## 参照ファイル

- `app/main.py`
- `app/api/v1/router.py`
- `libkoiki/api/v1/router.py`
- `docs/dev/v0.7-directory-reorganization-tasks.ja.md`

## 事前条件

- [Task 2-5](./task-2-5.md) が完了している

## 確認観点

- middleware
- router include
- DB 接続
- Redis
- background task
- SSO / SAML bootstrap

## 実施手順

1. `app.main` のトップレベル初期化を確認する
2. lifespan で行っている startup / shutdown 処理を列挙する
3. middleware / exception handler / monitoring の設定点を整理する
4. app 固有 router と `libkoiki` router の結合点を整理する
5. app factory 抽出時に分割すべき責務単位を記録する

## 成果物

- `app.main` の責務一覧
- app factory 抽出候補の分割メモ

## 検証

- `app.main` の責務一覧が抜けなく整理されている
- framework 共通 bootstrap と app 固有 bootstrap の境界が説明できる

## 完了条件

- Task 3-2 で `create_app()` の責務定義に進める

## 実施結果

Task:

- Task 3-1: 現行起動シーケンスの棚卸し

変更内容:

- `app/main.py` を読み、起動シーケンスの責務を次の7群に整理した
  - ロギング初期化
  - lifespan startup / shutdown
  - Redis / event publisher 初期化
  - rate limiter 初期化
  - middleware 設定
  - exception handler / monitoring 設定
  - router include と軽量 endpoint 定義
- `app.main` のトップレベル責務を次のように列挙した
  - `setup_logging()` を import 時に実行し、グローバル logger を構成する
  - Redis package 非導入時の dummy 実装を定義する
  - `SamlAuthFlowRepository` を import し、SAML cleanup task に利用する
  - `_periodic_saml_flow_cleanup()` を定義し、app 固有バックグラウンドタスクを持つ
  - `lifespan()` を定義し、startup / shutdown の全体制御を担う
  - `FastAPI(...)` で app インスタンスを直接生成する
  - middleware、exception handler、router、health/root endpoint をその場で登録する
- startup 側の責務を次のように整理した
  - DB 接続確認
    - `connect_db()`
  - Redis connection pool / client 初期化
    - `ConnectionPool.from_url(...)`
    - `Redis(...)`
    - `ping()`
  - event publisher 初期化
    - `EventPublisher(redis_client=app.state.redis)`
  - Redis 不可時の degraded 起動分岐
    - dummy redis / publisher
    - warning log
  - rate limiter 初期化
    - `Limiter(...)`
    - `app.state.limiter`
    - `RateLimitExceeded` handler
  - app 固有 background task 起動
    - `_periodic_saml_flow_cleanup()`
- shutdown 側の責務を次のように整理した
  - cleanup task の cancel / await
  - Redis client close
  - Redis pool disconnect
  - DB disconnect
- middleware / handler / monitoring 側の責務も整理した
  - middleware
    - `CORSMiddleware`
    - `SecurityHeadersMiddleware`
    - `AuditLogMiddleware`
    - `RequestContextLogMiddleware`
    - `AccessLogMiddleware` は未使用コメント
    - `SlowAPIMiddleware` は未使用コメント
  - exception handler
    - `setup_exception_handlers(app)`
  - monitoring
    - `setup_monitoring(app)` は import しているが現在は無効化コメント
- router 結合点を次のように整理した
  - app 固有 API
    - `app.api.v1.router`
    - `sso_auth`
    - `saml_auth`
    - `business_clock`
  - framework 標準 API
    - `libkoiki.api.v1.router`
    - `auth`
    - `users`
    - `todos`
    - `security_monitor`
  - どちらも `settings.API_PREFIX` 配下へ直接 include している
- SSO / SAML bootstrap の位置づけも確認した
  - `app.main` 自体は SSO / SAML service を直接初期化していない
  - ただし app 固有 router を include し、SAML cleanup task を起動しているため、app 固有認証 bootstrap の一部を担っている
  - したがって SSO / SAML は `create_app()` 内の app layer bootstrap に残すのが妥当
- app factory 抽出時に分割すべき責務単位を次のように整理した
  - framework helper 化候補
    - middleware registration helper
    - exception handler registration helper
    - monitoring setup helper
    - common Redis / limiter bootstrap helper
  - app layer に残す候補
    - app 固有 router include
    - SAML flow cleanup task
    - app 固有 degraded startup policy
  - `create_app()` 本体で束ねる候補
    - FastAPI instance creation
    - lifecycle wiring
    - common helper 呼び出し順制御
- 追加で、現行 `app.main` の構造上の問題点も整理した
  - import 時副作用で logging を初期化している
  - startup / shutdown の責務が長く、Redis・DB・limiter・background task が密結合
  - app 固有 bootstrap と framework 共通 bootstrap が同一ファイルに混在
  - monitoring が import されるが未使用で、構成の source of truth がぶれやすい
  - `todos` を含む framework router が app と同列で include されているため、reference / sample 境界の議論が必要

未解決事項:

- Redis / limiter bootstrap を framework helper へ寄せる範囲は、Task 3-2 で `create_app()` の責務と合わせて決める必要がある
- SAML cleanup task を app 固有 lifecycle module へ切り出すか、汎用 background task registry の形にするかは未決定
- monitoring の有効 / 無効を `create_app()` 引数で切り替えるか、settings ベースで閉じるかは未決定

検証結果:

- `app.main` の責務を startup、shutdown、middleware、router、background task の単位で抜けなく説明できる状態になった
- framework 共通 bootstrap と app 固有 bootstrap の境界が見えた
- Task 3-2 で `create_app()` の責務を定義するための分割単位が揃った

次タスクへ渡す事項:

- Task 3-2 では、`create_app()` を「FastAPI instance 作成 + lifecycle wiring + helper 呼び出し順制御」の中心に置く前提で設計する
- framework helper と app layer bootstrap の境界は、今回整理した責務単位をそのまま叩き台に使う

## 次タスク

- [Task 3-2](./task-3-2.md)
