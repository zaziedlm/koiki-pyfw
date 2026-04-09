# LOG-03 認証系ログ 追加洗い出し・実施結果

最終更新: 2026-04-09

## 1. 目的

本書は `LOG-03 認証・パスワード系ログの是正` の継続作業として、
`auth_token`、SSO、SAML を含む認証系ログの追加洗い出し結果と、
2026-04-09 時点での実施結果を整理したものである。

今回の観点は以下に限定する。

- 通常ログに不要な個人情報や機密性の高い値が残っていないか
- 本来 `security log` 側で扱うべきイベントを通常ログで過剰に記録していないか
- redirect URI、state/RelayState、login ticket など認証フロー固有の値を通常ログに出していないか

`security_logger` 自体のイベント粒度再設計は本書の対象外とし、`LOG-06` で扱う。

## 2. 現時点の前提

以下は `LOG-03` 着手前に対応済み。

- `libkoiki/core/logging.py` に共通 sanitizer 基盤を導入済み
- `auth_basic.py` と `auth_password.py` の通常ログから token / email / ip_address の過剰出力を一部除去済み

したがって、本書の主眼は「sanitizer がある前提でも、呼び出し側で削るべき通常ログ」を見つけることにある。

## 3. 実施サマリー

2026-04-09 時点で、`LOG-03` の対象としていた認証系通常ログの削減は
以下まで完了している。

- 完了:
  - [`auth_basic.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_basic.py)
  - [`auth_password.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_password.py)
  - [`sso_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/sso_auth.py)
  - [`saml_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/saml_auth.py)
  - [`sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/sso_service.py)
  - [`saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_service.py)
- 維持:
  - [`auth_token.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_token.py)
    - 現時点では `LOG-03` の追加修正対象外
- 未着手:
  - `security_logger` 自体のイベント粒度整理
  - `audit log` との役割分離の実装
  - これらは `LOG-06` `LOG-07` で扱う

## 4. 対応結果

## 4.1 `auth_token.py`

- 対象:
  - [`auth_token.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/libkoiki/api/v1/endpoints/auth_token.py)
- 現状評価:
  - 追加修正なし

### 所見

- `refresh` 開始・成功ログは message のみで、refresh token 自体を通常ログへ出していない
- `revoke-all-tokens` も `user_id`, `count` 中心で、通常ログとして妥当

### 実施結果

- 現時点では `LOG-03` の即時修正対象から外してよい
- ただし将来的に `refresh_token_rejected` を `security log` の限定イベントへ寄せる整理は `LOG-06` で検討対象

## 4.2 `sso_auth.py`

- 対象:
  - [`sso_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/sso_auth.py)
- 現状評価:
  - 対応完了

### 主な問題

1. 通常ログに `ip_address` と `device_info` を出している
   - `SSO login attempt`
   - `SSO login failed`
   - `Unexpected error during SSO login`

2. 通常ログに `email` を出している
   - `ID token verification successful`
   - `SSO user authentication successful`
   - `SSO login successful`

3. `ID token verification successful` で `sub` を通常ログに出している
   - `subject_id` は通常ログより security/audit 側の方が適切

### 実施結果

- 通常ログから `email`、`ip_address`、`device_info`、`sub` を削除済み
- 成功ログは `user_id`、`is_new_user` 中心へ縮小済み
- 失敗ログと例外ログは `status_code`、`error` 中心へ縮小済み
- `security_logger` 側には従来どおり `email`、`ip_address` を渡す構成を維持

### テスト

- [`test_sso_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py)
  - 成功時に通常 logger へ `email`、`ip_address`、`device_info`、`sub` が渡らないこと
  - `HTTPException` 時に通常 warning へ `ip_address` が渡らないこと
  - 想定外例外時に通常 error へ `ip_address` が渡らないこと

## 4.3 `saml_auth.py`

- 対象:
  - [`saml_auth.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/api/v1/endpoints/saml_auth.py)
- 現状評価:
  - 対応完了

### 主な問題

1. 通常ログに `redirect_uri` を出している
   - `SAML ACS processed successfully`

2. 通常ログに `subject_id` を出している
   - `SAML ACS processed successfully`
   - `SAML user info retrieved`

3. 通常ログに `ticket_expires`、`redirect` を出している
   - `SAML ACS processed successfully`
   - `SAML logout initiated`
   - `SAML SLS completed`

4. `saml_login` で通常ログに `ip_address`、`device_info`、`email` を出している
   - `SAML login attempt`
   - `SAML login successful`
   - `SAML login failed`
   - `Unexpected error during SAML login`

### 実施結果

- `ACS` 成功ログから `redirect_uri`、`subject_id`、`ticket_expires` を削除済み
- `saml_login` の通常ログから `email`、`ip_address`、`device_info` を削除済み
- `user-info`、`logout`、`SLS` の通常ログから `subject_id`、`redirect` を削除済み
- `security_logger` 側には従来どおり `email`、`ip_address` を渡す構成を維持

### テスト

- [`test_saml_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py)
  - `ACS` で protocol 値が通常 logger に出ないこと
  - `login` 成功/失敗/例外で `email`、`ip_address`、`device_info` が通常 logger に出ないこと
  - `user-info`、`logout`、`SLS` で `subject_id`、`redirect` が通常 logger に出ないこと

## 4.4 `sso_service.py`

- 対象:
  - [`sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/sso_service.py)
- 現状評価:
  - 対応完了

### 主な問題

1. 通常ログに `jwks_uri` を出している
   - `JWKS configured`

2. 通常ログに `email`, `sub` を出している
   - `ID token verification successful`
   - `Starting SSO user authentication`
   - `Creating new user from SSO`
   - `User auto-creation disabled`

3. 通常ログに `redirect_uri` を出している
   - `Generated authorization context`
   - `Redirect URI not allowed`

### 実施結果

- `JWKS configured` から `jwks_uri` を削除済み
- `ID token verification successful` から `email`、`sub` を削除済み
- `Generated authorization context` と `Redirect URI not allowed` から `redirect_uri` を削除済み
- `Starting SSO user authentication`、`Creating new user from SSO`、`User auto-creation disabled` から `email`、`sub` を削除済み
- `Failed to fetch JWKS` から `jwks_uri` を削除済み

### テスト

- [`test_sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_sso_service.py)
  - `generate_authorization_context` で `redirect_uri`、`nonce` が通常 logger に出ないこと
  - `verify_id_token` で `email`、`sub` が通常 logger に出ないこと
  - `authenticate_sso_user` で `email`、`sub` が通常 logger に出ないこと
  - `_ensure_redirect_uri_allowed` と `_fetch_jwks` で `redirect_uri`、`jwks_uri` が通常 logger に出ないこと

## 4.5 `saml_service.py`

- 対象:
  - [`saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/app/services/saml_service.py)
- 現状評価:
  - 対応完了

### 主な問題

1. 通常ログに `relay_state` を含む文脈値を出している
   - `Generated SAML authorization context`
   - 返却 context 自体に `relay_state` を含む箇所がある

2. 通常ログに `request_id`, `ticket_id`, `ticket_nonce`, `db_nonce` の断片を出している
   - `Starting SAML Response verification`
   - `relay_state nonce mismatch during ticket exchange`
   - `DB relay_nonce mismatch during ticket exchange`
   - `No DB flow found for ticket; falling back to in-memory check`

3. 通常ログに `email`, `subject_id`, `name_id`, `redirect` を出している
   - `SAML Response verification successful`
   - `Starting SAML user authentication`
   - `Creating new user from SAML`
   - `User auto-creation disabled`
   - `Generated SAML logout URL`
   - `SAML logout processed`

### 実施結果

- `Generated SAML authorization context` から `request_id`、`redirect_uri` を削除済み
- `Starting SAML Response verification` から `request_id` を削除済み
- `SAML Response verification successful` から `subject_id`、`email`、`session_index` を削除済み
- `Starting SAML user authentication`、`Creating new user from SAML`、`User auto-creation disabled` から `email`、`subject_id` を削除済み
- `relay_state nonce mismatch`、`DB relay_nonce mismatch`、`No DB flow found for ticket` から `nonce`、`ticket` 断片を削除済み
- logout service / cleanup から `redirect`、`name_id` を削除済み

### テスト

- [`test_saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)
  - `generate_authn_request` で `request_id`、`redirect_uri` が通常 logger に出ないこと
  - `verify_saml_response` で `subject_id`、`email`、`session_index` が通常 logger に出ないこと
  - `authenticate_saml_user` で `email`、`subject_id` が通常 logger に出ないこと
  - `exchange_login_ticket` で `relay_nonce`、`ticket_id` 断片が通常 logger に出ないこと
  - logout service / cleanup で `redirect`、`name_id` が通常 logger に出ないこと

## 5. `LOG-03` で追加したテスト

- [`test_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/libkoiki/api/test_auth_logging.py)
- [`test_sso_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_sso_auth_logging.py)
- [`test_saml_auth_logging.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/test_saml_auth_logging.py)
- [`test_sso_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_sso_service.py)
- [`test_saml_service.py`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/tests/unit/app/services/test_saml_service.py)

## 6. 残課題

`LOG-03` の範囲としては、通常ログから危険値を減らす作業は完了した。
ただし、以下は本タスクの対象外として残している。

- `security_logger` の限定イベント定義と粒度整理
- `audit log` との責務分離
- `request context` や相関IDと結びついた監査整備
- 認証系以外の入力データログ是正

これらは `LOG-04` `LOG-06` `LOG-07` で扱う。

## 7. 次アクション

1. `LOG-03` の作業計画としては完了扱いにする
2. `auth_token.py` は現状維持とし、`LOG-06` で `security log` 側の扱いだけ再確認する
3. 次の実装タスクは `LOG-04` または `LOG-06` へ進める
4. warning は [`WARNING_FOLLOWUP_TASKS_ja.md`](C:/Users/kataoka/Desktop/KOIKI-FW/KOIKI-FW-VSCodeProj/koiki-pyfw/docs/backend-audit/WARNING_FOLLOWUP_TASKS_ja.md) で別管理する

## 8. 補足

- 本書の初版では「洗い出し結果」を記録していたが、
  2026-04-09 時点で対象箇所の通常ログ削減と単体テスト追加が完了したため、
  現在は実施結果を含む進捗文書として扱う。
