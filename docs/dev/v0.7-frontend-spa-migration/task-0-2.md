# Task 0-2: backend 認証 contract 設計

## 目的

SPA が依存する backend auth API contract を定義し、Next.js route handler の責務を FastAPI 側へ移す前提を固める。

## 参照ファイル

- `components/libkoiki/src/libkoiki/api/v1/endpoints/auth*.py`
- `components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/sso_auth.py`
- `components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/saml_auth.py`
- `components/libkoiki/src/libkoiki/services/auth_service.py`
- `components/koiki_ref_app/src/koiki_ref_app/services/sso_service.py`
- `components/koiki_ref_app/src/koiki_ref_app/services/saml_service.py`

## 事前条件

- Task 0-1 が完了している

## Contract 候補

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/csrf`
- `GET /api/v1/auth/sso/authorization`
- `POST /api/v1/auth/sso/login`
- `GET /api/v1/auth/saml/authorization`
- `POST /api/v1/auth/saml/login`

## 必須決定事項

- 既存の token-returning endpoint を維持するか、Cookie 認証用 endpoint を新設するか
- login request を JSON にするか、現行の form-urlencoded `OAuth2PasswordRequestForm` を維持するか
- login / refresh / SSO / SAML login の response body から token value を除外する条件
- refresh token を request body から受け取るか、`HttpOnly` Cookie から受け取るか
- register 成功時に自動ログインするか、現行どおり再ログインを要求するか
- logout 時に Cookie clear のみ行うか、現在の refresh token 失効まで行うか
- Users API の BFF authorization parity を backend 側でどう維持するか
- CSRF を要求する request の条件
  - Cookie 認証された state-changing request を対象にする
  - Bearer-token client を壊さない
- SSO / SAML exchange endpoint の CSRF 要否
  - `state`, `nonce`, PKCE, RelayState, one-time ticket, Origin check と合わせて判断する
- same-origin / cross-origin 方針
  - CSRF token transport
  - CORS
  - Cookie `SameSite`
  - Cookie `Secure`
  - `__Host-*` prefix の可否
- env migration 方針
  - `VITE_*` に残すもの
  - backend setting へ移すもの
  - 削除するもの
- auth cookie 名、max-age、secure attributes の source of truth

## 実施手順

1. 既存 backend endpoint の request / response を確認する
2. Cookie 発行が必要な endpoint を決める
3. CSRF が必要な endpoint を決める
4. refresh token rotation と logout 失効の仕様を確認する
5. SSO / SAML callback URL の互換要件を確認する
6. frontend から見た API contract を文書化する
7. 既存 Bearer client / integration test との互換性を確認する
8. BFF authorization parity を backend contract に反映する

## 推奨成果物

- endpoint contract 表
  - method
  - path
  - request body / content-type
  - Cookie input / output
  - response body
  - CSRF 要否
  - auth policy
- Cookie 名、属性、max-age の定義
- CSRF token 取得・送信方式
- CORS / same-origin 方針
- env mapping 表
  - current env
  - `VITE_*`
  - backend setting
  - removed
- Users API authorization parity decision

## 検証

- SPA が token value を扱わずに動作できる contract になっている
- Cookie 認証された state-changing request の CSRF 要件が明確である
- 既存 non-browser / Bearer client を壊す変更が明示的に判断されている
- origin / CSRF / Cookie 属性の組み合わせが矛盾していない

## 完了条件

- Task 1-1 以降で実装する backend 変更範囲が確定している
- 未決の contract decision が Task 1 系の実装に持ち越されていない

## 実施結果

未実施。
