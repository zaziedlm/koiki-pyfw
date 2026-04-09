# LOG-08 回帰防止テスト追加

最終更新: 2026-04-09

## 1. 目的

`LOG-08` は、`LOG-02` から `LOG-07` までで導入した logging 改善を、
回帰防止テストとして継続運用できる形へ整理する作業である。

本タスクの目的は以下。

- 個別タスクで追加した test を policy 観点で束ね直す
- 「どのリスクをどの test が守るか」を明文化する
- 代表的な cross-layer 挙動をまとめて検証する実行セットを定義する

## 2. 方針

### 2.1 テスト設計の考え方

- helper / sanitizer / logger API は unit test で守る
- endpoint / service の logger 引数は unit test で守る
- middleware / request context / audit 配線は TestClient ベースの cross-layer test で守る
- DB 依存や実アプリ wiring まで必要なものは integration test 候補として整理する

### 2.2 今回の対象

- [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
- [`tests/unit/core/test_security_logger.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_security_logger.py)
- [`tests/unit/core/test_audit_middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_audit_middleware.py)
- [`tests/unit/libkoiki/api/test_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
- [`tests/unit/libkoiki/test_input_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_input_logging.py)
- [`tests/unit/libkoiki/test_error_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_error_logging.py)
- [`tests/unit/libkoiki/test_audit_dependencies.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_audit_dependencies.py)
- [`tests/unit/libkoiki/test_token_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_token_logging.py)
- [`tests/unit/app/test_sso_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py)
- [`tests/unit/app/test_saml_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py)
- [`tests/unit/app/services/test_saml_support_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_support_logging.py)
- [`tests/unit/app/services/test_sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_sso_service.py)
- [`tests/unit/app/services/test_saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)

## 3. カバレッジ整理

### 3.1 共通 sanitizer / logging 基盤

対象:

- `sanitize_mapping`
- `sanitize_event_dict`
- `get_log_field_names`
- `get_error_type_name`
- `normal / security / audit` のカテゴリ分岐

主な test:

- [`test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
- [`test_token_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_token_logging.py)

守っているリスク:

- token / password / secret の再流出
- token 断片ログの再流出
- email / ip_address / user_agent の通常ログ生値化
- cycle / depth / nested payload の処理崩れ

### 3.2 security logger の限定イベント

対象:

- `security_logger` の許可イベント制御
- auth_method / failure_reason に応じた event type 正規化
- allowlist 以外の field 排除

主な test:

- [`test_security_logger.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_security_logger.py)

守っているリスク:

- 未許可イベントの security log 混入
- 任意 field の過剰出力
- password / SSO / SAML のイベント粒度崩れ

### 3.3 認証系 endpoint / service の通常ログ是正

対象:

- password login
- password reset
- refresh token rejection
- SSO login
- SAML login
- SSO / SAML service

主な test:

- [`test_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
- [`test_sso_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py)
- [`test_saml_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py)
- [`test_sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_sso_service.py)
- [`test_saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)

守っているリスク:

- email / ip_address / sub / subject_id の通常ログ残存
- reset token / relay_state / login ticket の露出
- refresh token rejection が security log に残らないこと

### 3.4 入力データ / 例外ログ是正

対象:

- repository / service の raw input logging
- DB 例外 / validation / HTTPException の raw detail logging

主な test:

- [`test_input_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_input_logging.py)
- [`test_error_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_error_logging.py)
- [`test_saml_support_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_support_logging.py)

守っているリスク:

- `__dict__` や payload 丸ごとの露出
- `str(exc)` や validation input の露出
- metadata / certificate / metrics 周辺での raw error 文字列露出

### 3.5 audit / request context 配線

対象:

- `RequestContextLogMiddleware`
- `AuditLogMiddleware`
- `AccessLogMiddleware`
- `get_current_active_user()` による `request.state` 配線

主な test:

- [`test_audit_middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_audit_middleware.py)
- [`test_audit_dependencies.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_audit_dependencies.py)

守っているリスク:

- `X-Request-ID` の不整合
- audit log に query / header / secret が混入すること
- actor 情報が audit log に入らないこと

## 4. LOG-08 で追加した補強

- audit middleware が query string や `Authorization` / `Cookie` を audit payload に含めないことを追加確認
- request context / audit / access の cross-layer 確認を回帰セットへ固定
- 認証依存が `request.state.current_user` と `request.state.auth_method` を設定する確認を追加
- `LOG-10` で追加した token 断片非出力と raw exception 非出力の観点を回帰セットへ追加

## 5. 推奨実行セット

### 5.1 最小回帰セット

```powershell
poetry run pytest `
  tests/unit/core/test_logging_sanitizer.py `
  tests/unit/core/test_security_logger.py `
  tests/unit/core/test_audit_middleware.py `
  tests/unit/libkoiki/api/test_auth_logging.py `
  tests/unit/libkoiki/test_input_logging.py `
  tests/unit/libkoiki/test_error_logging.py `
  tests/unit/libkoiki/test_audit_dependencies.py `
  tests/unit/libkoiki/test_token_logging.py `
  tests/unit/app/test_sso_auth_logging.py `
  tests/unit/app/test_saml_auth_logging.py `
  tests/unit/app/services/test_saml_support_logging.py `
  tests/unit/app/services/test_sso_service.py `
  tests/unit/app/services/test_saml_service.py
```

### 5.2 変更単位ごとの推奨実行

- sanitizer 変更時:
  - `test_logging_sanitizer.py`
  - `test_token_logging.py`
  - `test_security_logger.py`
- auth endpoint 変更時:
  - `test_auth_logging.py`
  - `test_sso_auth_logging.py`
  - `test_saml_auth_logging.py`
- audit / middleware 変更時:
  - `test_audit_middleware.py`
  - `test_audit_dependencies.py`
- service logging 変更時:
  - `test_saml_support_logging.py`
  - `test_sso_service.py`
  - `test_saml_service.py`
  - `test_error_logging.py`

## 6. 未完了

- DB 実接続を使った logging integration test の整備
- CI workflow への regression set 組み込み
- `LOG-09` での運用向け test 実行手順整備

## 7. 2026-04-09 時点の固定結果

確認済みコマンド:

```powershell
poetry run pytest `
  tests/unit/core/test_logging_sanitizer.py `
  tests/unit/core/test_security_logger.py `
  tests/unit/core/test_audit_middleware.py `
  tests/unit/libkoiki/api/test_auth_logging.py `
  tests/unit/libkoiki/test_input_logging.py `
  tests/unit/libkoiki/test_error_logging.py `
  tests/unit/libkoiki/test_audit_dependencies.py `
  tests/unit/libkoiki/test_token_logging.py `
  tests/unit/app/test_sso_auth_logging.py `
  tests/unit/app/test_saml_auth_logging.py `
  tests/unit/app/services/test_saml_support_logging.py `
  tests/unit/app/services/test_sso_service.py `
  tests/unit/app/services/test_saml_service.py
```

結果:

- `125 passed`
- 既知 warning のみ発生

- 既知 warning の参照先:
  - [`WARNING_FOLLOWUP_TASKS_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/WARNING_FOLLOWUP_TASKS_ja.md)

## 8. 次アクション

1. `LOG-08` は最小回帰セット整理まで完了扱いにする
2. 次は `LOG-09` の運用・保守向け文書更新へ進む
3. CI へどのセットを入れるかは別途 workflow 側で整理する
