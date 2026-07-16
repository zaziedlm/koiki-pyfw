# Task 1-1: backend Cookie / CSRF primitives

## 目的

FastAPI 側に Cookie 発行、Cookie clearing、CSRF token 発行・検証の共通 primitive を用意する。

## 配置方針

- reusable な Cookie / CSRF helper は `components/libkoiki/`
- reference app 固有の SSO / SAML wiring は `components/koiki_ref_app/`

## 事前条件

- Task 0-2 が完了している

## 実施手順

1. Cookie 設定 helper の既存有無を確認する
2. access token cookie と refresh token cookie の属性を実装する
3. auth cookie clearing helper を実装する
4. CSRF token 発行 helper を実装する
5. Cookie 認証に対応する current-user dependency を設計する
   - `Authorization: Bearer` を維持する
   - Bearer がない場合に access token Cookie を読む
   - 既存 client の互換性を壊さない
6. CSRF 検証 dependency または middleware を実装する
   - Cookie 認証された state-changing request に限定する
   - safe method には要求しない
   - non-browser Bearer-token client には要求しない
7. Cookie 設定の source of truth を backend config に置く
   - cookie name
   - max-age
   - `Secure`
   - `SameSite`
   - `Domain` / host-only
   - `__Host-*` prefix の利用条件
8. token exp と Cookie max-age の整合性を確認する
9. raw token をログ出力しないことを確認する

## 検証

- unit test で Cookie 属性を確認できる
- invalid CSRF が拒否される
- safe method に CSRF を要求しない
- Bearer-token client に CSRF を要求しない
- Cookie 認証で current user を解決できる
- token exp と Cookie max-age の不整合が説明可能である

## 完了条件

- password auth endpoint から再利用できる Cookie / CSRF primitive が揃っている
- Task 1-2 / Task 1-3 が独自に Cookie / CSRF logic を再実装しなくてよい

## 実施結果

実施済み。

### 実装内容

- `components/libkoiki/src/libkoiki/core/config.py`
  - auth Cookie / CSRF Cookie 名、`Secure`、`SameSite`、`Domain`、`Path`、CSRF max-age を backend settings に追加した。
  - `AUTH_COOKIE_SAMESITE` は `lax` / `strict` / `none` のみ許可する validator を追加した。
- `components/libkoiki/src/libkoiki/core/auth_cookies.py`
  - access token Cookie / refresh token Cookie の set helper を追加した。
  - auth Cookie / CSRF Cookie の clear helper を追加した。
  - access Cookie max-age は `ACCESS_TOKEN_EXPIRE_MINUTES`、refresh Cookie max-age は `REFRESH_TOKEN_EXPIRE_DAYS` に合わせた。
- `components/libkoiki/src/libkoiki/core/csrf.py`
  - signed CSRF token 生成 helper を追加した。
  - JS-readable CSRF Cookie 発行 helper を追加した。
  - Cookie 認証された unsafe method だけを対象にする CSRF 検証 helper を追加した。
  - invalid CSRF は HTTP 403 と stable code `CSRF_TOKEN_INVALID` で拒否する。
- `components/libkoiki/src/libkoiki/core/security.py`
  - `Authorization: Bearer` を優先し、Bearer がない場合だけ access token Cookie を読むようにした。
  - request state に `auth_method` として `bearer` / `cookie` を記録するようにした。
  - 既存 token decode logic を `decode_access_token_user_id()` として分離した。
  - 内部 helper の古い直接呼び出し互換は残さず、既存 unit test を `decode_access_token_user_id()` の検証へ寄せた。
- `components/libkoiki/src/libkoiki/api/dependencies.py`
  - `ActiveUserDep` が `auth_method` を保持するようにした。
  - endpoint 側で再利用できる `CookieCSRFDep` を追加した。

### 検証

- 追加 unit test:
  - `components/libkoiki/tests/unit/core/test_auth_cookie_csrf.py`
- 実行コマンド:
  - `DEBUG=False uv run pytest components/libkoiki/tests/unit/core/test_auth_cookie_csrf.py`
  - `DEBUG=False uv run pytest tests/unit/test_pyjwt_migration.py components/libkoiki/tests/unit/libkoiki/api/test_auth_logging.py components/libkoiki/tests/unit/libkoiki/test_token_logging.py components/libkoiki/tests/unit/core/test_auth_cookie_csrf.py`
- 結果:
  - 追加 test 単体: 7 passed
  - 既存 auth 周辺を含む確認: 49 passed
  - PyJWT の HMAC key length warning は既存 development secret 長に由来する警告。

### 確認結果

- Cookie 属性は backend settings から設定される。
- CSRF は Cookie 認証された unsafe method だけで要求される。
- safe method と Bearer-token request では CSRF を要求しない。
- current user 解決では Bearer token が優先され、Bearer がない場合のみ access token Cookie fallback になる。
- Task 1-2 / Task 1-3 が独自に Cookie / CSRF logic を再実装せずに使える primitive が揃った。
