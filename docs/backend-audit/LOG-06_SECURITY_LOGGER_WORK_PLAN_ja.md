# LOG-06 security logger 情報粒度再設計

最終更新: 2026-04-09

## 1. 目的

`LOG-06` は、`security_logger` をポリシー準拠の限定イベントロガーへ整理し、
通常ログとは異なる粒度でセキュリティイベントを安定して記録できるようにする作業である。

本タスクの主目的は以下。

- `security log` に流してよいイベント種別をコードで固定する
- `security log` に残してよいフィールドを共通化する
- 認証系 endpoint が `security_logger` に渡す情報をポリシーへ合わせる
- 将来の `LOG-07` で audit log と役割分離しやすい形へ整える

## 2. 対応方針

### 2.1 基本方針

- `libkoiki/core/security_logger.py` に許可イベント一覧を定数化する
- `log_security_event()` は許可されていない event type を拒否する
- `log_authentication_attempt()` は従来の呼び出し API を維持しつつ、
  内部では `authentication_failed_invalid_credentials` などの限定イベントへ正規化する
- 出力フィールドは allowlist で絞り、`additional_data` の任意項目をそのまま出さない

### 2.2 今回の対象

- [`libkoiki/core/security_logger.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security_logger.py)
- [`libkoiki/api/v1/endpoints/auth_basic.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_basic.py)
- [`tests/unit/core/test_security_logger.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_security_logger.py)
- [`tests/unit/libkoiki/api/test_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
- [`tests/unit/core/test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)

## 3. 実施内容

### LOG-06-01 許可イベントの定数化

- `security_logger.py` に以下を定数化した
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

### LOG-06-02 許可フィールドの allowlist 化

- `ALLOWED_SECURITY_FIELDS` を導入した
- `additional_data` の任意項目はそのまま出さず、以下に限定した
  - `request_id`
  - `user_id`
  - `username`
  - `email`
  - `ip_address`
  - `user_agent`
  - `endpoint`
  - `auth_method`
  - `failure_reason`
  - `lockout_duration`
  - `count`
  - `threshold`
  - `sso_provider`
  - `saml_provider`
  - `subject_id`

### LOG-06-03 既存 API の互換維持と内部正規化

- `log_authentication_attempt()` は公開 API を維持
- 内部で `auth_method`、`success`、`failure_reason` から event type を決定する形へ変更
- password login の成功は `authentication_succeeded_after_risk_check`
- password login の失敗は `authentication_failed_invalid_credentials` または `authentication_failed_inactive_user`
- SSO / SAML の成功失敗は `sso_login_succeeded` / `sso_login_failed`、`saml_login_succeeded` / `saml_login_failed` へ正規化

### LOG-06-04 auth_basic の配線補正

- `auth_method=password` を明示するよう補正
- inactive user 失敗時にも `security_logger` と `security_metrics` を記録するよう補正
- lockout イベントも `failure_reason` を明示して記録するよう補正

### LOG-06-05 password reset / refresh token rejection 接続

- [`auth_password.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_password.py)
  に以下を接続した
  - 既存ユーザー向け password reset request 成功時:
    `password_reset_requested_existing_user`
  - password reset confirm 成功時:
    `password_reset_completed`
  - password reset token 不正時:
    `password_reset_rejected_invalid_token`
- [`auth_token.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_token.py)
  に以下を接続した
  - refresh token 不正形式、失効済み、期限切れ、ユーザー無効等による拒否時:
    `refresh_token_rejected`

### LOG-06-06 回帰テスト追加

- [`test_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
  に以下を追加した
  - password reset request が security event を発火すること
  - password reset complete が security event を発火すること
  - invalid reset token が `password_reset_rejected_invalid_token` で記録されること
  - refresh token rejection が `refresh_token_rejected` で記録されること

## 4. 実施結果

完了済み:

- `security_logger` が許可イベント以外を受け付けない状態へ変更
- `security log` に流れるフィールドが allowlist で制限された
- password / SSO / SAML の認証イベントがポリシーの限定イベント名へ正規化された
- password login の inactive user が `security log` に残るようになった
- password reset request / complete / invalid token rejection が `security log` に接続された
- refresh token rejection が `security log` に接続された

未完了:

- `LOG-07` で audit log と責務分離を明確化すること

## 5. テスト

実行済みコマンド:

```powershell
poetry run pytest tests/unit/core/test_security_logger.py tests/unit/core/test_logging_sanitizer.py tests/unit/libkoiki/api/test_auth_logging.py tests/unit/app/test_sso_auth_logging.py tests/unit/app/test_saml_auth_logging.py
```

確認済み観点:

- password login 失敗が `authentication_failed_invalid_credentials` へ正規化されること
- inactive user が `authentication_failed_inactive_user` へ正規化されること
- password login 成功が `authentication_succeeded_after_risk_check` へ正規化されること
- SSO / SAML 成功失敗が provider-specific event type へ正規化されること
- lockout と rate limit が限定イベント名で記録されること
- password reset request / complete / invalid token が限定イベント名で記録されること
- refresh token rejection が限定イベント名で記録されること
- unsupported event type が `ValueError` で拒否されること
- sanitizer と組み合わせた smoke test が維持されること

## 6. 次アクション

1. `LOG-06` は完了扱いとし、以降は `LOG-07` へ進む
2. `LOG-07` として audit log との責務分離と監査項目固定へ進む
3. `security_logger` の保存先分離は実運用配線と合わせて別途確認する
