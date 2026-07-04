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

既存 token-returning endpoint:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

SPA Cookie session endpoint:

- `GET /api/v1/auth/session/csrf`
- `POST /api/v1/auth/session/login`
- `POST /api/v1/auth/session/register`
- `POST /api/v1/auth/session/refresh`
- `POST /api/v1/auth/session/logout`
- `GET /api/v1/auth/session/me`
- `POST /api/v1/auth/session/sso/login`
- `POST /api/v1/auth/session/saml/login`

Direct browser flow endpoint:

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

実施済み。

### Contract decision summary

- 既存 token-returning endpoint は non-browser / Bearer client 向け互換 contract として維持する。
- SPA 用には Cookie session endpoint を新設し、browser は token value を response body で受け取らない。
- 既存 `/api/v1/auth/login` は form-urlencoded `OAuth2PasswordRequestForm` + `TokenWithRefresh` のまま維持する。
- SPA login は JSON request の Cookie session endpoint を使う。
- registration は現行どおり register-then-login とし、register 成功時の自動ログインは行わない。
- refresh は Cookie session endpoint では `HttpOnly` refresh Cookie から読む。既存 `/auth/refresh` は body `{ refresh_token }` を維持する。
- Cookie session logout は auth Cookie clear に加え、可能な場合は現在の refresh token を失効する。既存 Bearer `/auth/logout` は現行互換を維持する。
- CSRF は Cookie 認証された unsafe method に要求する。Bearer-token client には要求しない。
- SSO / SAML の browser session exchange も Cookie を発行する state-changing request なので CSRF を要求する。加えて `state` / `nonce` / PKCE / RelayState / one-time ticket / Origin check を維持する。
- production は same-origin 配信を推奨 default とする。cross-origin 配信は明示 CORS origin、credentialed request、Cookie `SameSite=None; Secure` が揃う場合のみ許容する。
- auth cookie / CSRF cookie の name、max-age、secure attributes は backend settings を source of truth とする。
- Users API は BFF 削除で権限が緩まないように、`POST /users` を admin / permission protected に寄せる。public registration は `/auth/register` 系に限定する。

### Endpoint contract

#### Existing token endpoints retained for compatibility

| Method | Path | Request | Cookie input / output | Response body | CSRF | Auth policy |
| --- | --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | `application/x-www-form-urlencoded`, `username`, `password` | none | `TokenWithRefresh` with `access_token`, `refresh_token`, `token_type`, `expires_in` | no | public login, existing rate limit / LoginSecurityService / security logging preserved |
| POST | `/api/v1/auth/register` | JSON `UserCreate` | none | `AuthResponse` with user info, no tokens | no | public registration, existing rate limit preserved |
| POST | `/api/v1/auth/refresh` | JSON `{ refresh_token }` | none | `TokenWithRefresh` | no | public token refresh with refresh token validation |
| POST | `/api/v1/auth/logout` | none | Bearer token only | `AuthResponse` | no | existing Bearer current user |
| GET | `/api/v1/auth/me` | none | Bearer token only | `UserResponse` | no | existing Bearer current user |
| POST | `/api/v1/auth/sso/login` | JSON `SSOLoginRequest` | none | `TokenWithRefresh` | no | public SSO exchange with state / nonce / PKCE validation |
| POST | `/api/v1/auth/saml/login` | JSON `SAMLLoginTicketRequest` | none | `TokenWithRefresh` | no | public SAML ticket exchange with RelayState / ticket validation |

#### New browser Cookie session endpoints

| Method | Path | Request | Cookie input / output | Response body | CSRF | Auth policy |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/auth/session/csrf` | none | sets / rotates JS-readable CSRF cookie if using double-submit mode | `{ csrf_token, header_name }` | no | public bootstrap |
| POST | `/api/v1/auth/session/login` | JSON `{ email \| username, password }` | sets access, refresh, CSRF cookies | `{ message, user, location }`, no token values | yes | public login, same security checks as `/auth/login` |
| POST | `/api/v1/auth/session/register` | JSON `UserCreate` | no auth cookies by default; may rotate CSRF cookie | `{ message, user, location }`, no token values | yes | public registration, no auto-login |
| POST | `/api/v1/auth/session/refresh` | none | reads refresh Cookie; rotates access / refresh / CSRF cookies; clears auth cookies on failure | `{ message }`, no token values | yes | refresh token Cookie required |
| POST | `/api/v1/auth/session/logout` | none | reads refresh Cookie when present; clears access / refresh / CSRF cookies | `{ message }` | yes | succeeds even if access token is expired; revokes current refresh token when identifiable |
| GET | `/api/v1/auth/session/me` | none | reads access Cookie | `UserResponse` | no | Cookie current user |
| POST | `/api/v1/auth/session/sso/login` | JSON SSO exchange payload | sets access, refresh, CSRF cookies | `{ message, user?, location }`, no token values | yes | state / nonce / PKCE validation plus Origin check when available |
| POST | `/api/v1/auth/session/saml/login` | JSON `{ login_ticket, relay_state }` | sets access, refresh, CSRF cookies | `{ message, user?, location }`, no token values | yes | RelayState / one-time ticket validation plus Origin check when available |

#### Direct browser endpoints reused by SPA

| Method | Path | Request | Cookie input / output | Response body | CSRF | Auth policy |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/auth/sso/authorization` | optional `redirect_uri` | none required | existing `SSOAuthorizationInitResponse` | no | public, rate limited |
| GET | `/api/v1/auth/saml/authorization` | optional `redirect_uri` | may create backend SAML state records | existing `SAMLAuthorizationInitResponse` | no | public, rate limited |
| GET/POST | Todo and User read endpoints | existing query/body | access Cookie or Bearer | existing backend response | no for safe methods | Active user / permission checks |
| POST/PUT/PATCH/DELETE | Todo and User state-changing endpoints | existing JSON body | access Cookie or Bearer | existing backend response | required only when auth source is Cookie | Active user / permission checks |

### Cookie definition

| Cookie | Default name | HttpOnly | JS readable | Default max-age | SameSite | Secure | Path | Source of truth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Access token | `koiki_access_token` | yes | no | align with `ACCESS_TOKEN_EXPIRE_MINUTES` | default `Lax` | production true | `/` | backend settings |
| Refresh token | `koiki_refresh_token` | yes | no | align with `REFRESH_TOKEN_EXPIRE_DAYS` | default `Lax` | production true | `/` | backend settings |
| CSRF token | `koiki_csrf_token` | no | yes | 24 hours default | match auth cookie deployment mode | production true when required | `/` | backend settings |

Default cookie names remain `koiki_*` for compatibility with existing frontend behavior and local HTTP development.
`__Host-*` names are a future hardening option only when HTTPS, `Secure`, `Path=/`, and no `Domain` can be guaranteed.
Do not set broad `Domain` by default; use host-only cookies unless a deployment-specific reason is documented.

### CSRF contract

- CSRF applies to Cookie-authenticated `POST`, `PUT`, `PATCH`, and `DELETE`.
- CSRF does not apply to safe `GET` requests.
- CSRF does not apply to Bearer-token clients unless a separate explicit policy is introduced.
- CSRF bootstrap endpoint returns the token in response body and sets the CSRF cookie.
- SPA sends the token in `x-csrf-token`.
- Backend validates a signed double-submit style token. The implementation may compare cookie/header after signature validation, but raw token values must not be logged.
- Login, refresh, SSO session login, and SAML session login rotate or reissue CSRF token after successful Cookie changes.
- Missing or invalid CSRF returns stable error code `CSRF_TOKEN_INVALID` with HTTP 403.
- SPA may retry once after `CSRF_TOKEN_INVALID` by refreshing CSRF token.

### Origin, CORS, and deployment contract

Default target:

- production: same-origin SPA and API preferred
- local development: cross-origin `http://localhost:5173` -> `http://localhost:8000` allowed explicitly

Same-origin deployment:

- CORS disabled or minimal
- host-only cookies
- `SameSite=Lax`
- production `Secure=true`
- `__Host-*` can be considered after local compatibility is solved

Cross-origin deployment:

- `BACKEND_CORS_ORIGINS` must list exact frontend origins
- `Access-Control-Allow-Credentials` must be enabled
- wildcard origin is not allowed for credentialed requests
- cross-site browser deployment requires `SameSite=None; Secure`
- Origin check is required for Cookie session state-changing endpoints when an `Origin` header is present

### Users API authorization parity decision

`POST /api/users` in the current Next.js BFF is admin-only, while backend `POST /users` is currently public.
Removing the BFF would otherwise make user creation less restrictive.

Decision:

- Public self-registration remains under `/api/v1/auth/register` and `/api/v1/auth/session/register`.
- Backend `POST /api/v1/users` becomes admin / permission protected in the v0.8 breaking-change line.
- Backend `GET /users`, `GET /users/{id}`, `PUT /users/{id}`, and `DELETE /users/{id}` continue to use permission checks, but Task 1 implementation must verify that role `admin` / `is_superuser` parity with the BFF is preserved by default data/permissions.
- `/users/me` remains active-user only.

### Env mapping

| Current env | Vite SPA env | Backend setting | Removed / notes |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `VITE_API_URL` only if cross-origin direct API is needed | deployment may instead use same-origin API path | replace `NEXT_PUBLIC_*` prefix |
| `NEXT_PUBLIC_API_PREFIX` | `VITE_API_PREFIX` | `API_PREFIX` | replace `NEXT_PUBLIC_*` prefix |
| `NEXT_PUBLIC_API_BASE_URL` | `VITE_API_BASE_URL` for cross-origin local/dev | prefer backend or same-origin reverse proxy in production | replace `NEXT_PUBLIC_*` prefix |
| `BACKEND_API_URL` in frontend server routes | none | backend internal service URL / compose networking | remove from SPA; no frontend server runtime |
| `BACKEND_API_PREFIX` in frontend server routes | none | `API_PREFIX` | remove from SPA |
| `NEXT_PUBLIC_ALLOWED_ORIGINS` | none | `BACKEND_CORS_ORIGINS` / explicit frontend origins | security policy belongs to backend |
| `NEXT_PUBLIC_COOKIE_AUTH_ENABLED` | none | session endpoint availability setting if needed | remove; SPA always uses Cookie session contract |
| `NEXT_PUBLIC_ACCESS_TOKEN_NAME` | none | backend auth cookie name setting | remove from SPA; auth Cookie is HttpOnly |
| `NEXT_PUBLIC_REFRESH_TOKEN_NAME` | none | backend refresh cookie name setting | remove from SPA; refresh Cookie is HttpOnly |
| `NEXT_PUBLIC_COOKIE_SAMESITE` | none | backend cookie SameSite setting | remove from SPA |
| `NEXT_PUBLIC_COOKIE_SECURE` | none | backend cookie Secure setting | remove from SPA |
| `NEXT_PUBLIC_SSO_REDIRECT_URI` | `VITE_SSO_REDIRECT_URI` | SSO allowed redirect URI / default redirect URI | keep public callback path only |
| `NEXT_PUBLIC_SAML_REDIRECT_URI` | `VITE_SAML_REDIRECT_URI` | SAML allowed redirect URI / default redirect URI | keep public callback path only |
| `NEXT_PUBLIC_APP_NAME` | `VITE_APP_NAME` | optional `APP_NAME` for backend docs | keep public display value |
| `NEXT_PUBLIC_APP_VERSION` | `VITE_APP_VERSION` | optional backend version separately | keep public display value |
| `NEXT_PUBLIC_ENABLE_DEV_TOOLS` | `VITE_ENABLE_DEV_TOOLS` | none | dev-only public flag |
| `NEXT_PUBLIC_DEBUG` | `VITE_DEBUG` | backend `DEBUG` remains boolean | do not leak backend debug policy |
| `NEXT_PUBLIC_API_TIMEOUT` | `VITE_API_TIMEOUT` | none | client-only timeout |
| `NEXT_PUBLIC_ENABLE_SECURITY_HEADERS` | none | backend / static server headers config | remove from SPA runtime |

### Implementation scope for Task 1

- Add backend Cookie settings.
- Add Cookie set / clear helpers in `components/libkoiki/`.
- Add CSRF bootstrap and validation primitives in `components/libkoiki/`.
- Add current-user dependency support for Bearer first, then access Cookie fallback.
- Mark request auth source so CSRF can apply only to Cookie-authenticated unsafe requests.
- Add `/auth/session/*` Cookie endpoints for password auth in `components/libkoiki/`.
- Add `/auth/session/sso/login` and `/auth/session/saml/login` wiring in `components/koiki_ref_app/`.
- Restrict backend `POST /users` to preserve BFF admin-only behavior.
- Add integration tests that prove Bearer compatibility and Cookie/CSRF behavior.

### Verification

- SPA can complete login, refresh, logout, current user resolution, SSO exchange, and SAML exchange without receiving token values in response bodies.
- Existing token-returning endpoints remain available for non-browser clients.
- Cookie-authenticated unsafe requests require CSRF.
- Bearer-token clients do not require CSRF.
- Same-origin default and cross-origin exception rules are explicit.
- Users API BFF authorization parity is captured as implementation scope.
