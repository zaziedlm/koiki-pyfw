# LOG-07 監査ログ方針との整合化

最終更新: 2026-04-09

## 1. 目的

`LOG-07` は、audit log をポリシーに沿った最小項目で安定して記録できる状態へ整える作業である。

本タスクの主目的は以下。

- `RequestContextLogMiddleware` を実際に配線する
- `AuditLogMiddleware` が request context と認証状態から audit payload を組み立てられるようにする
- `request_id` をリクエストとレスポンス、通常ログ、audit log で一貫させる
- audit log に不要な query や secret を載せないようにする

## 2. 対応方針

### 2.1 基本方針

- request context は `libkoiki/core/logging.py` の contextvar を source of truth とする
- audit log は `actor.*`, `client.*`, `http.*`, `target.*`, `action`, `outcome`, `duration_ms` を基本形とする
- 認証済みユーザー情報は `request.state.current_user` から取得する
- 認証方式は `request.state.auth_method` から取得する
- raw query や request body は audit log へ入れない

### 2.2 今回の対象

- [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
- [`libkoiki/core/middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/middleware.py)
- [`libkoiki/api/dependencies.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/dependencies.py)
- [`app/main.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/main.py)
- [`tests/unit/core/test_audit_middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_audit_middleware.py)
- [`tests/unit/libkoiki/test_audit_dependencies.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_audit_dependencies.py)

## 3. 実施内容

### LOG-07-01 request context の取得経路統一

- `logging.py` に `get_request_context()` を追加
- `AuditLogMiddleware` と `AccessLogMiddleware` が `structlog.contextvars` ではなく、
  実際に使っている contextvar から request context を読むように変更

### LOG-07-02 RequestContext middleware の実配線

- [`app/main.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/main.py)
  に `RequestContextLogMiddleware` を追加
- FastAPI の middleware ラップ順に合わせて、
  `AuditLogMiddleware` より外側で動くよう追加順を調整
- `X-Request-ID` が未指定でも生成され、レスポンスへ返るようにした

### LOG-07-03 audit payload の最小化

- `AuditLogMiddleware` の payload を以下へ整理
  - `actor.user_id`
  - `actor.email`
  - `actor.auth_method`
  - `client.ip_address`
  - `http.method`
  - `http.path`
  - `http.request_id`
  - `http.status_code`
  - `target.resource_type`
  - `target.resource_id`
  - `action`
  - `outcome`
  - `duration_ms`
- raw query は audit payload から除外
- path params があれば `target.resource_type` と `target.resource_id` を設定

### LOG-07-04 認証依存からの actor 情報連携

- [`libkoiki/api/dependencies.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/dependencies.py)
  の `get_current_active_user()` で、認証成功時に以下を設定
  - `request.state.current_user`
  - `request.state.auth_method = "bearer"`

## 4. 実施結果

完了済み:

- request context と audit / access log の取得経路が一致した
- `X-Request-ID` が audit log へ反映されるようになった
- audit log が actor / client / http / target / action / outcome / duration の最小項目へ整理された
- query を audit log に載せないようにした
- 認証依存から `actor.user_id`, `actor.email`, `actor.auth_method` を audit log へ流せる状態になった

未完了:

- audit log の保存先分離と write/read 権限分離
- 重要操作ごとの `target.resource_type` / `target.resource_id` の精密化
- `LOG-09` での運用手順明文化

## 5. テスト

実行済みコマンド:

```powershell
poetry run pytest tests/unit/core/test_audit_middleware.py tests/unit/core/test_logging_sanitizer.py tests/unit/libkoiki/api/test_auth_logging.py
```

追加確認:

```powershell
poetry run pytest tests/unit/libkoiki/test_audit_dependencies.py
```

確認済み観点:

- `X-Request-ID` が生成され、audit log に同じ値が入ること
- 受信した `X-Request-ID` が維持されること
- health など除外パスが audit log へ流れないこと
- access log が同じ request context source を使うこと
- 認証依存が `request.state.current_user` と `request.state.auth_method` を設定すること

## 6. 次アクション

1. `LOG-07` は最小配線完了として扱う
2. 次は `LOG-08` の回帰防止テスト整理、または `LOG-09` の運用文書整備へ進む
3. audit log の保存先分離はインフラ設定と合わせて別途確認する
