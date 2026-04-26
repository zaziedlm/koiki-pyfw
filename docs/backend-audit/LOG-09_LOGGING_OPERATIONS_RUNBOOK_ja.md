# LOG-09 運用・保守向け文書更新

最終更新: 2026-04-09

## 1. 目的

本書は、`LOG-02` から `LOG-08` までで整備した logging / security log / audit log の実装を、
運用担当・保守担当が実際に扱うための runbook として整理したものである。

本書の目的は以下。

- 通常ログ、security log、audit log の使い分けを明確にする
- 障害解析、認証インシデント対応、監査対応の確認順序を統一する
- 保守時の実行コマンド、確認観点、変更時レビュー観点を残す

## 2. 前提

この runbook は、以下の文書と実装を前提とする。

- ポリシー:
  - [`BACKEND_LOGGING_SECURITY_POLICY_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/BACKEND_LOGGING_SECURITY_POLICY_ja.md)
- 実装計画:
  - [`LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-06_SECURITY_LOGGER_WORK_PLAN_ja.md)
  - [`LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-07_AUDIT_LOG_ALIGNMENT_WORK_PLAN_ja.md)
  - [`LOG-08_LOGGING_REGRESSION_TEST_PLAN_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/LOG-08_LOGGING_REGRESSION_TEST_PLAN_ja.md)

## 3. ログの役割分担

### 3.1 通常ログ

用途:

- 障害の一次切り分け
- API や service の処理失敗把握
- 例外発生箇所の特定

見るべき項目:

- `message`
- `request_id`
- `status_code`
- `user_id`
- `error_type`

見てはいけない前提:

- email / ip_address / user_agent の生値
- token / password / secret

運用上の注意:

- 通常ログに機密値が出ていた場合は bug とみなす
- query string や request body を通常ログで追おうとしない

### 3.2 Security Log

用途:

- 認証失敗
- lockout
- password reset
- refresh token rejection
- SSO / SAML 認証異常

主な event type:

- `authentication_failed_invalid_credentials`
- `authentication_failed_inactive_user`
- `authentication_blocked_lockout`
- `authentication_succeeded_after_risk_check`
- `refresh_token_rejected`
- `password_reset_requested_existing_user`
- `password_reset_completed`
- `password_reset_rejected_invalid_token`
- `sso_login_failed`
- `sso_login_succeeded`
- `saml_login_failed`
- `saml_login_succeeded`
- `token_reuse_or_integrity_violation_detected`
- `suspicious_activity_detected`
- `rate_limit_exceeded_security_sensitive_endpoint`

見るべき項目:

- `event_type`
- `request_id`
- `email`
- `ip_address`
- `user_agent`
- `auth_method`
- `failure_reason`

運用上の注意:

- 許可イベント以外が security log に出ていたら実装逸脱
- token 本体や token 断片が出ていたら即時インシデント扱い

### 3.3 Audit Log

用途:

- 監査証跡
- 重要操作の追跡
- 認証済みユーザー操作の確認

見るべき項目:

- `actor.user_id`
- `actor.email`
- `actor.auth_method`
- `client.ip_address`
- `http.method`
- `http.path`
- `http.request_id`
- `target.resource_type`
- `target.resource_id`
- `action`
- `outcome`
- `duration_ms`

運用上の注意:

- audit log は通常ログの代用ではない
- query string や request body を audit log に求めない
- actor 情報が空のまま重要操作が記録される場合は配線不備を疑う

## 4. 代表的な運用シナリオ

### 4.1 ログイン失敗が増えている

確認順序:

1. security log で `authentication_failed_invalid_credentials` の件数を見る
2. `ip_address` と `email` の偏りを見る
3. `authentication_blocked_lockout` の発生有無を見る
4. 通常ログで同じ `request_id` の error / warning を確認する

判断ポイント:

- 単一 IP に偏るなら攻撃疑い
- 単一 email に偏るならアカウント標的化の疑い
- lockout まで出ていれば rate limit / security control は機能している

### 4.2 refresh token 異常が発生した

確認順序:

1. security log で `refresh_token_rejected` を検索する
2. `failure_reason` を確認する
3. 通常ログで同一 `request_id` の例外や `error_type` を確認する
4. 必要なら対象 user の revoke 実施状況を audit log で確認する

判断ポイント:

- 形式不正が多いならクライアント不具合または攻撃試行
- 期限切れ / 無効化済みが多いならクライアント再試行や端末残存トークンの疑い

### 4.3 password reset 異常が発生した

確認順序:

1. security log で以下を確認する
   - `password_reset_requested_existing_user`
   - `password_reset_completed`
   - `password_reset_rejected_invalid_token`
2. `email`, `ip_address`, `failure_reason` を確認する
3. 通常ログで同一 `request_id` の例外を確認する

判断ポイント:

- request だけ多く complete が極端に少ないなら不正試行または配送経路問題
- invalid token が急増していれば token 取扱い不備または攻撃試行を疑う

### 4.4 SSO / SAML 障害が発生した

確認順序:

1. security log で `sso_login_failed` または `saml_login_failed` を確認する
2. `failure_reason`, `ip_address`, `subject_id` の有無を確認する
3. 通常ログで `error_type` と `request_id` を確認する
4. audit log で成功イベントが継続しているかを確認する

判断ポイント:

- 失敗が全面的なら外部 IdP 側または設定異常の疑い
- 一部 user のみなら subject mapping / local user linkage の疑い

### 4.5 監査対応で操作証跡を確認したい

確認順序:

1. audit log で `actor.user_id` または `actor.email` を基点に検索する
2. 期間を絞って `http.path`, `action`, `outcome` を確認する
3. 詳細な障害要因が必要なら `http.request_id` で通常ログと突き合わせる

判断ポイント:

- audit log は「誰が何をしたか」の証跡
- 失敗理由の詳細は通常ログまたは security log で補完する

## 5. 日常運用チェック

### 5.1 デプロイ後の確認

最低限見ること:

- `X-Request-ID` がレスポンスに返る
- 通常ログに token / password / email / ip_address の生値が出ていない
- 認証系操作で security log が event type 付きで出る
- 認証済み API で audit log に `actor.user_id` が入る

### 5.2 障害一次切り分け時の確認

最低限見ること:

- 同じ `request_id` を基点に通常ログ、security log、audit log を横断できるか
- `error_type` が十分に出ているか
- query / body / secret がログに混入していないか

### 5.3 リリース前レビュー時の確認

レビュー対象:

- 新しい logger 呼び出しが raw payload を渡していないか
- `security_logger.log_security_event()` に未許可 event type を使っていないか
- audit log に request body, query, secret を載せていないか

## 6. 推奨テスト実行手順

### 6.1 logging 周辺をまとめて確認する場合

```powershell
uv run --locked pytest `
  components/libkoiki/tests/unit/core/test_logging_sanitizer.py `
  components/libkoiki/tests/unit/core/test_security_logger.py `
  components/libkoiki/tests/unit/core/test_audit_middleware.py `
  components/libkoiki/tests/unit/libkoiki/api/test_auth_logging.py `
  components/libkoiki/tests/unit/libkoiki/test_input_logging.py `
  components/libkoiki/tests/unit/libkoiki/test_error_logging.py `
  components/libkoiki/tests/unit/libkoiki/test_audit_dependencies.py `
  components/koiki_ref_app/tests/unit/app/test_sso_auth_logging.py `
  components/koiki_ref_app/tests/unit/app/test_saml_auth_logging.py `
  components/koiki_ref_app/tests/unit/app/services/test_sso_service.py `
  components/koiki_ref_app/tests/unit/app/services/test_saml_service.py
```

### 6.2 変更単位ごとの最小実行

- sanitizer / formatter を変えた場合:
  - `components/libkoiki/tests/unit/core/test_logging_sanitizer.py`
  - `components/libkoiki/tests/unit/core/test_security_logger.py`
- audit / middleware を変えた場合:
  - `components/libkoiki/tests/unit/core/test_audit_middleware.py`
  - `components/libkoiki/tests/unit/libkoiki/test_audit_dependencies.py`
- auth endpoint / service を変えた場合:
  - `components/libkoiki/tests/unit/libkoiki/api/test_auth_logging.py`
  - `components/koiki_ref_app/tests/unit/app/test_sso_auth_logging.py`
  - `components/koiki_ref_app/tests/unit/app/test_saml_auth_logging.py`
  - `components/koiki_ref_app/tests/unit/app/services/test_sso_service.py`
  - `components/koiki_ref_app/tests/unit/app/services/test_saml_service.py`

## 7. 既知の残課題

運用上の既知事項:

- warning は現時点で 0 件ではない
- 既知 warning は以下
  - Pydantic v1 style validator 非推奨
  - `LoginAttemptModel` の SQLAlchemy warning
  - 一部 `.dict()` 非推奨

参照:

- [`WARNING_FOLLOWUP_TASKS_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/WARNING_FOLLOWUP_TASKS_ja.md)

未実装事項:

- audit log の保存先分離
- write/read 権限分離
- logging regression set の CI 組み込み

## 8. 変更管理メモ

logging 周辺を変更したときは、最低限以下を更新対象とする。

- 実装コード
- 対応する unit test
- 必要に応じて policy / work plan / runbook

ドキュメント更新の判断基準:

- event type を追加・変更した
- 許可 field を追加・変更した
- audit payload の項目を変更した
- 運用上の確認手順が変わった

## 9. 次アクション

1. 本書を `LOG-09` の成果物として扱う
2. CI workflow へ regression set をどう入れるかは別タスクで整理する
3. warning 解消は [`WARNING_FOLLOWUP_TASKS_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/WARNING_FOLLOWUP_TASKS_ja.md) に従って別管理する
