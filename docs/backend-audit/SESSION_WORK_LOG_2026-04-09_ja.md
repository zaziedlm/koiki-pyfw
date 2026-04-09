# セッション作業ログ 2026-04-09

対象リポジトリ: `koiki-pyfw`  
対象テーマ: Enterprise 品質点検、ログセキュリティ改善、Docker/E2E 検証  
記録日: 2026-04-09

## 1. セッション概要

本セッションでは、既存の Enterprise 品質点検結果を見直したうえで、
ログセキュリティ改善を中心に、方針策定、作業計画、実装、unit test、
Docker `prod` profile 上の E2E 検証までを実施した。

最終的に、以下を完了した。

- backend-audit 文書群の新規作成・整理
- 共通 log sanitizer 基盤の実装
- 認証、入力、例外、security logger、audit log の段階的改善
- token 断片ログと raw exception 文字列ログの除去
- Docker `unified-prod-build` / `unified-prod` での SAML / OIDC / 管理ログイン E2E 確認
- E2E 起点で見つかった残件の是正と完了確認

## 2. Enterprise 品質点検

### 2.1 初期レビュー

実施内容:

- 既存レポートに引きずられず、コードベースを基準に Enterprise 品質観点で再点検
- 元レポートの妥当性確認
- 新規観点の追加

主な結論:

- 設定・秘密情報統制
- トランザクション整合性
- 監査 / 監視
- CI / テスト品質

が主要リスク領域であると整理した。

### 2.2 点検レポート作成

作成・更新した文書:

- [BACKEND_ENTERPRISE_AUDIT_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/BACKEND_ENTERPRISE_AUDIT_ja.md)
- [BACKEND_LOGGING_SECURITY_POLICY_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md)

内容:

- 重要度
- 元レポート記載有無
- 問題点
- Enterprise 品質上の懸念
- 修正方針
- 優先着手順

## 3. 文書整理

`docs/` 配下の audit 関連文書を整理し、専用フォルダへ移動した。

配置:

- [docs/backend-audit/](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit)

## 4. ログセキュリティ方針策定

### 4.1 ポリシー確定

主な決定事項:

- 通常ログ:
  - `email` は部分マスク
  - `ip_address` は部分マスク
  - `user_agent` は通常ログでは保持しない方針
- security log:
  - 限定イベントのみ
  - `email` / `ip_address` の生値保持可
- audit log:
  - 生値保持可
  - ただし権限制御前提
- `libkoiki` を基盤に、`app/` の SSO / SAML へ適用

作成文書:

- [BACKEND_LOGGING_SECURITY_POLICY_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md)

## 5. LOG-02 共通 log sanitizer 基盤

### 5.1 計画

作成文書:

- [LOG-02_COMMON_LOG_SANITIZER_WORK_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-02_COMMON_LOG_SANITIZER_WORK_PLAN_ja.md)

明文化した点:

- キー正規化
- 広すぎる禁止キーの扱い
- 再帰打ち切り条件

### 5.2 実装

主な変更:

- [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
  - `mask_email`
  - `mask_ip_address`
  - `mask_user_agent`
  - `is_sensitive_key`
  - `sanitize_log_value`
  - `sanitize_mapping`
  - `sanitize_event_dict`
  - logger category 解決

テスト:

- [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)

## 6. LOG-03 認証系ログ是正

### 6.1 対象

- [`libkoiki/api/v1/endpoints/auth_basic.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_basic.py)
- [`libkoiki/api/v1/endpoints/auth_password.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_password.py)
- [`app/api/v1/endpoints/sso_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/sso_auth.py)
- [`app/api/v1/endpoints/saml_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/saml_auth.py)
- [`app/services/sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/sso_service.py)
- [`app/services/saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_service.py)

### 6.2 是正内容

- reset token 平文ログ削除
- token 断片ログ削除
- 通常ログから `email`, `ip_address`, `sub`, `subject_id`, `redirect_uri`, `device_info` などを除去
- SSO / SAML の通常ログを最小限へ縮小

作成文書:

- [LOG-03_AUTH_LOGGING_FINDINGS_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-03_AUTH_LOGGING_FINDINGS_ja.md)

## 7. LOG-04 入力データログ是正

### 7.1 対象

- [`libkoiki/repositories/base.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/repositories/base.py)
- [`libkoiki/services/user_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/user_service.py)
- [`libkoiki/services/todo_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/todo_service.py)
- [`app/repositories/user_sso_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/user_sso_repository.py)
- [`libkoiki/events/handlers.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/events/handlers.py)
- [`libkoiki/events/publisher.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/events/publisher.py)
- [`libkoiki/utils/email.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/utils/email.py)
- [`libkoiki/tasks/email.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/tasks/email.py)

### 7.2 是正内容

- `__dict__` 丸出し停止
- raw payload logging 停止
- `provided_fields` / `payload_fields` / `update_fields` ベースへ統一

作成文書:

- [LOG-04_INPUT_LOGGING_WORK_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-04_INPUT_LOGGING_WORK_PLAN_ja.md)

## 8. LOG-05 例外 / DB ログ是正

### 8.1 対象

- [`libkoiki/core/error_handlers.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/error_handlers.py)
- [`libkoiki/db/session.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/db/session.py)
- [`libkoiki/core/auth_decorators.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/auth_decorators.py)
- [`libkoiki/core/transaction.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/transaction.py)
- SSO / SAML 関連 service / endpoint

### 8.2 是正内容

- `error=str(e)` を `error_type` に統一
- validation / DB error の detail を最小化
- raw exception 文字列の通常ログ出力を一掃

作成文書:

- [LOG-05_EXCEPTION_LOGGING_WORK_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-05_EXCEPTION_LOGGING_WORK_PLAN_ja.md)

## 9. LOG-06 security logger

### 9.1 実施内容

- security event を限定イベント化
- allowlist ベースで field 制御
- password login / password reset / refresh token rejection を security event に接続

作成文書:

- [LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md)

## 10. LOG-07 audit log 整備

### 10.1 実施内容

- [`libkoiki/core/middleware.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/middleware.py)
  の request context / audit payload 整理
- [`libkoiki/api/dependencies.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/dependencies.py)
  で `request.state.current_user` / `auth_method` を配線
- [`app/main.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/main.py)
  の middleware 順序整理

作成文書:

- [LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md)

## 11. LOG-08 回帰テスト整理

### 11.1 実施内容

- logging 改善一式の回帰セットを定義
- helper / security logger / auth endpoint / service / audit middleware の test を束ね直し

作成文書:

- [LOG-08_LOGGING_REGRESSION_TEST_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-08_LOGGING_REGRESSION_TEST_PLAN_ja.md)

## 12. LOG-09 運用 runbook

### 12.1 作成文書

- [LOG-09_LOGGING_OPERATIONS_RUNBOOK_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-09_LOGGING_OPERATIONS_RUNBOOK_ja.md)

内容:

- 通常ログ / security log / audit log の使い分け
- 障害対応シナリオ
- リリース前確認
- 日常運用観点

## 13. LOG-10 最終 hardening

### 13.1 実施内容

- token 本体 / token 断片ログ除去
- `error=str(e)` 系の最終掃除
- regression set への固定

作成文書:

- [LOG-10_FINAL_LOGGING_HARDENING_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-10_FINAL_LOGGING_HARDENING_PLAN_ja.md)

## 14. warning 別タスク化

### 14.1 作成文書

- [WARNING_FOLLOWUP_TASKS_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/WARNING_FOLLOWUP_TASKS_ja.md)

切り出した内容:

- `LoginAttemptModel` の SQLAlchemy warning
- Pydantic v1 style validator 非推奨
- reload 起因の warning 増幅

## 15. Docker / E2E 検証

### 15.1 方針

Docker / ECS 寄せ構成に合わせ、以下を基準手順とした。

- `.\start-docker.ps1 unified-prod-build`
- `.\start-docker.ps1 unified-prod`
- `docker compose -f docker-compose.unified.yml --profile prod logs app-prod --tail=300`

### 15.2 初回 E2E で見つかった課題

- Uvicorn access log の query string 漏えい
- SAML の `relay_nonce` / `ticket_id` 断片ログ
- normal log の `request.http.client` / `request.http.user_agent`
- `JWT_SECRET` 長さ warning
- `passlib/bcrypt` 由来 traceback

### 15.3 LOG-11

作成文書:

- [LOG-11_E2E_LOGGING_REMEDIATION_PLAN_ja.md](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-11_E2E_LOGGING_REMEDIATION_PLAN_ja.md)

実施内容:

- [`Dockerfile.unified`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/Dockerfile.unified)
  の `uvicorn --no-access-log`
- [`libkoiki/core/logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py)
  で normal log の `request.http` を `method/path/request_id` のみに制限
- [`app/repositories/saml_auth_flow_repository.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/repositories/saml_auth_flow_repository.py)
  の断片ログ除去
- 追加 unit test と再 E2E

### 15.4 E2E 最終確認結果

確認したログイン経路:

- OIDC SSO
- SAML
- フレームワーク管理ログイン

確認結果:

- query string は Uvicorn access log に残らない
- SAML の nonce / ticket 断片ログは残らない
- normal log に `request.http.client` / `request.http.user_agent` は残らない
- security log / audit log は必要情報を保持

結論:

- 第 1 弾ログセキュリティ対応は、E2E まで含めて完了扱い

## 16. 主な追加 / 更新テスト

- [test_logging_sanitizer.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
- [test_security_logger.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_security_logger.py)
- [test_audit_middleware.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_audit_middleware.py)
- [test_auth_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
- [test_input_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_input_logging.py)
- [test_error_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_error_logging.py)
- [test_audit_dependencies.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_audit_dependencies.py)
- [test_token_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_token_logging.py)
- [test_sso_auth_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py)
- [test_saml_auth_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py)
- [test_saml_support_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_support_logging.py)
- [test_sso_service.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_sso_service.py)
- [test_saml_service.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)
- [test_saml_auth_flow_repository_logging.py](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/repositories/test_saml_auth_flow_repository_logging.py)

## 17. セッション終了時点の残課題

今回のログセキュリティ第 1 弾の完了後も、次は別タスクで扱うべきもの:

- [`JWT_SECRET`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/.env.production) の長さ是正
- `passlib/bcrypt` 由来 traceback
- `audit / security handler` 分離
- CI への regression set 組み込み
- warning 解消

## 18. 補足

本ファイルは、このセッションの会話ログの生データではなく、
実施内容を後追いできるように整理した作業記録である。
