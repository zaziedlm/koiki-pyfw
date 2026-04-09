# LOG-10 ログセキュリティ最終 Hardening 計画

最終更新: 2026-04-09

## 1. 目的

本書は、logging 改善の最終スコープを以下の 2 点に絞って完了させるための計画である。

- token 本体・token 断片ログの完全除去
- `error=str(e)` 系の raw exception 文字列ログの一掃

本計画の完了をもって、今回の `ログセキュリティ / マスク対応` の第 1 弾を完了扱いとする。

## 2. 今回の対象範囲

### 2.1 対象

- 通常ログに残っている token 本体、token 断片、token 類推可能なログ
- 通常ログに残っている raw exception 文字列
- 上記を防ぐ回帰テスト

### 2.2 対象外

今回の計画では、以下は実施対象外とする。

- `audit log` と `security log` の handler / 保存先分離
- logging regression set の CI 組み込み
- warning 解消
- stack trace 全文の sanitizer 対応

## 3. 現時点の残課題

### 3.1 token 断片ログ

代表的な残件:

- [`auth_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/auth_service.py)
  - `token_prefix=refresh_token[:10] + "..."`
- [`security.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security.py)
  - `token=token[:10] + "..."`

### 3.2 raw exception 文字列ログ

代表的な残件:

- [`sso_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/sso_auth.py)
- [`saml_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/saml_auth.py)
- [`saml_metadata_loader.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_metadata_loader.py)
- [`saml_certificate_manager.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_certificate_manager.py)
- [`security_metrics.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security_metrics.py)
- [`users.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/users.py)

## 4. 作業単位

### LOG-10-01 token 断片ログ除去

- 目的:
  - token 本体だけでなく token 断片も通常ログから除去する
- 主対象:
  - [`auth_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/auth_service.py)
  - [`security.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security.py)
- 対応方針:
  - `token_prefix` や `token[:10]` のような断片出力を削除する
  - 通常ログは `user_id`, `error_type`, `status`, `rotation_enabled` など最小限へ寄せる
  - 必要なら `sanitize_log_value()` 側にも token 派生キーのガードを追加する
- 完了条件:
  - 通常ログに token 本体も token 断片も出ない
- 状況:
  - 完了

### LOG-10-02 raw exception 文字列ログ一掃

- 目的:
  - `error=str(e)` や f-string での例外文字列ログを `error_type` 系へ統一する
- 主対象:
  - [`sso_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/sso_auth.py)
  - [`saml_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/saml_auth.py)
  - [`saml_metadata_loader.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_metadata_loader.py)
  - [`saml_certificate_manager.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_certificate_manager.py)
  - [`security_metrics.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security_metrics.py)
  - [`users.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/users.py)
- 対応方針:
  - 共通 helper `get_error_type_name()` を使い、`error_type` に統一する
  - user-facing `HTTPException.detail` は維持し、内部ログとは分離する
  - 外部連携失敗時も URL、XML、署名関連メッセージの生文字列を通常ログへ出さない
- 完了条件:
  - 通常ログに raw exception 文字列が残らない
- 状況:
  - 完了

### LOG-10-03 回帰テスト追加

- 目的:
  - `LOG-10-01` と `LOG-10-02` の再発防止
- 主対象:
  - [`test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py)
  - [`test_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
  - [`test_error_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_error_logging.py)
  - [`test_sso_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py)
  - [`test_saml_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py)
  - [`test_sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_sso_service.py)
  - [`test_saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)
- 対応方針:
  - token 断片が logger 引数に渡らないことを固定する
  - `error=str(e)` 相当の raw error を logger に渡さないことを固定する
  - 既存 sanitizer と合わせて regression set に含める
- 完了条件:
  - 最小回帰セットで `LOG-10` 観点が自動確認できる
- 状況:
  - 完了

## 5. 実施順

1. `LOG-10-01`
2. `LOG-10-02`
3. `LOG-10-03`

理由:

- token 断片は機密度が高く、最優先で止めるべき
- その後に raw exception を横展開で掃除する
- 最後に回帰テストで固定する

## 6. 推奨テスト単位

### 6.1 LOG-10-01 実施後

```powershell
poetry run pytest `
  tests/unit/core/test_logging_sanitizer.py `
  tests/unit/libkoiki/api/test_auth_logging.py
```

### 6.2 LOG-10-02 実施後

```powershell
poetry run pytest `
  tests/unit/libkoiki/test_error_logging.py `
  tests/unit/app/test_sso_auth_logging.py `
  tests/unit/app/test_saml_auth_logging.py `
  tests/unit/app/services/test_saml_support_logging.py `
  tests/unit/app/services/test_sso_service.py `
  tests/unit/app/services/test_saml_service.py
```

### 6.3 LOG-10 完了確認

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

## 7. 完了判定

今回のログセキュリティ対応は、以下を満たした時点で完了扱いとする。

- token 本体・token 断片が通常ログに残らない
- `error=str(e)` / f-string 例外文字列ログが通常ログに残らない
- 既存 regression set に `LOG-10` の観点が組み込まれている
- `audit/security handler 分離は今回対象外` であることが文書上も明確

## 8. 2026-04-09 時点の進捗

完了済み:

- [`auth_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/services/auth_service.py) の `token_prefix` ログを除去
- [`security.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security.py) の token 断片ログを除去
- [`logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/logging.py) に `token_prefix` を機密キーとして追加
- [`test_logging_sanitizer.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/core/test_logging_sanitizer.py) に token 派生キーの防御テストを追加
- [`test_token_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_token_logging.py) を追加し、service / security helper の token 断片非出力を固定
- [`sso_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/sso_auth.py) の raw exception logging を `error_type` へ統一
- [`saml_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/saml_auth.py) の raw exception logging を `error_type` へ統一
- [`saml_metadata_loader.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_metadata_loader.py) の raw exception logging を `error_type` へ統一
- [`saml_certificate_manager.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_certificate_manager.py) の raw exception logging を `error_type` へ統一
- [`security_metrics.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security_metrics.py) の raw exception logging を `error_type` へ統一
- [`users.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/users.py) の validation error logging を `error_type` へ統一
- [`security.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/core/security.py) の `extract_device_info()` 例外ログを `error_type` へ統一
- [`test_sso_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py) に SSO endpoint / health の `error_type` 固定テストを追加
- [`test_saml_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py) に SAML endpoint / health の `error_type` 固定テストを追加
- [`test_saml_support_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_support_logging.py) を追加し、metadata loader / certificate manager の `error_type` 固定テストを追加
- [`test_error_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/test_error_logging.py) に security metrics / users endpoint / `extract_device_info()` の `error_type` 固定テストを追加

確認済みコマンド:

```powershell
poetry run pytest tests/unit/core/test_logging_sanitizer.py tests/unit/libkoiki/test_token_logging.py
poetry run pytest tests/unit/app/test_sso_auth_logging.py tests/unit/app/test_saml_auth_logging.py tests/unit/app/services/test_saml_support_logging.py tests/unit/libkoiki/test_error_logging.py
poetry run pytest tests/unit/core/test_logging_sanitizer.py tests/unit/core/test_security_logger.py tests/unit/core/test_audit_middleware.py tests/unit/libkoiki/api/test_auth_logging.py tests/unit/libkoiki/test_input_logging.py tests/unit/libkoiki/test_error_logging.py tests/unit/libkoiki/test_audit_dependencies.py tests/unit/libkoiki/test_token_logging.py tests/unit/app/test_sso_auth_logging.py tests/unit/app/test_saml_auth_logging.py tests/unit/app/services/test_saml_support_logging.py tests/unit/app/services/test_sso_service.py tests/unit/app/services/test_saml_service.py
```

次の着手対象:

- なし（`LOG-10` 完了）

## 9. 次アクション

1. 今回のログセキュリティ対応は完了扱いとする
2. コメント内の旧 `error=str(e)` 表記は必要に応じて後で掃除する
3. warning 解消や CI 組み込みは別タスクで管理する
