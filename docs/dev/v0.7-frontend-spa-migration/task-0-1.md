# Task 0-1: frontend 責務棚卸し

## 目的

現行 `frontend/` の Next.js 実装が担っている UI 責務と server/BFF 責務を分離して、移行漏れを防ぐ。

## 参照ファイル

- `frontend/src/app/`
- `frontend/src/app/api/`
- `frontend/src/middleware.ts`
- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/lib/cookie-utils.ts`
- `frontend/src/lib/csrf-utils.ts`
- `frontend/src/hooks/`
- `frontend/package.json`

## 事前条件

- `docs/dev/frontend-spa-migration-plan.ja.md` を読んでいる

## 実施手順

1. `frontend/src/app/api/**/route.ts` を一覧化する
2. 各 route handler の backend 移管要否を分類する
3. `next/link`、`next/navigation`、`next/server` 依存箇所を一覧化する
4. browser storage 利用箇所を一覧化する
5. Next.js 削除前に backend parity が必要な処理を抽出する
6. BFF が追加している authorization check を抽出する
   - 特に `/api/users` GET/POST の admin check を backend 側で維持するか確認する

## 推奨成果物

- route handler ごとの移管表
- UI 移植対象ファイル一覧
- Next.js 依存 API の置換表
- BFF authorization parity 表
  - route
  - BFF 側 check
  - backend 側 check
  - 移管後の期待 policy

## 検証

- API route handler 16 件がすべて分類されている
- Cookie / CSRF / refresh / SSO / SAML の移管先が説明できる
- BFF 削除で権限が緩む route が未分類で残っていない

## 完了条件

- Task 0-2 の backend contract 設計に必要な現状情報が揃っている

## 実施結果

実施済み。

### API route handler 棚卸し

現行 `frontend/src/app/api/**/route.ts` は 16 件。

| Route handler | Method | 現行 BFF 責務 | Backend 移管先 / 対応方針 |
| --- | --- | --- | --- |
| `/api/auth/login` | POST | CSRF 検証、JSON login request を backend form-urlencoded `/auth/login` へ変換、access / refresh Cookie 発行、CSRF rotate、redirect 用 response shaping | FastAPI が browser login contract、Cookie 発行、CSRF rotate を直接担う。既存 form-urlencoded token endpoint を維持するか Cookie 用 endpoint を新設するかは Task 0-2 で決定する。 |
| `/api/auth/register` | POST | CSRF 検証、`/auth/register` proxy、backend が token を返す場合の Cookie 発行、CSRF rotate | FastAPI が register contract を担う。register 後 auto-login するか、現行どおり register-then-login とするかは Task 0-2 で決定する。 |
| `/api/auth/refresh` | POST | CSRF 検証、refresh Cookie から token を読み body `{ refresh_token }` に変換、refresh 失敗時 Cookie clear、成功時 Cookie rotate、CSRF rotate | FastAPI が refresh Cookie input、token rotation、Cookie clear / rotate、CSRF rotate を担う。既存 body contract 維持要否は Task 0-2 で決定する。 |
| `/api/auth/logout` | POST | CSRF 検証、access Cookie を Bearer として backend `/auth/logout` へ proxy、backend error を握りつぶして Cookie clear | FastAPI が logout Cookie clear と必要な refresh token 失効を担う。失効範囲は Task 0-2 で決定する。 |
| `/api/auth/me` | GET | access Cookie を Bearer に変換して `/auth/me` へ proxy | FastAPI dependency が Bearer と access Cookie の両方から current user を解決できるようにする。 |
| `/api/auth/csrf` | GET | CSRF token 生成、JS-readable CSRF Cookie 発行、body に `csrf_token` を返す | FastAPI が CSRF bootstrap を担う。Cookie transport / response body transport は origin 方針と合わせて Task 0-2 で決定する。 |
| `/api/todos` | GET | access Cookie を Bearer に変換し `/todos` へ proxy、query string 転送 | FastAPI `/todos` が Cookie 認証 current user に対応すれば SPA が直接呼べる。 |
| `/api/todos` | POST | CSRF 検証、access Cookie を Bearer に変換し `/todos` へ proxy | FastAPI `/todos` が Cookie 認証と Cookie 認証 state-changing request の CSRF 検証に対応する。 |
| `/api/todos/[id]` | GET | access Cookie を Bearer に変換し `/todos/{id}` へ proxy | FastAPI `/todos/{id}` が Cookie 認証 current user に対応する。 |
| `/api/todos/[id]` | PUT | CSRF 検証、access Cookie を Bearer に変換し `/todos/{id}` へ proxy | FastAPI `/todos/{id}` が Cookie 認証と CSRF 検証に対応する。 |
| `/api/todos/[id]` | DELETE | CSRF 検証、access Cookie を Bearer に変換し `/todos/{id}` へ proxy、成功 body を `{ message }` に整形 | FastAPI `/todos/{id}` が Cookie 認証と CSRF 検証に対応する。DELETE response shape 差分は frontend 側で吸収するか contract に含める。 |
| `/api/users` | GET | access Cookie を Bearer に変換、`/auth/me` で current user を取得し admin check、backend `/users` へ proxy | Backend 側の `read:users` permission と BFF admin check の parity を Task 0-2 で確認する。 |
| `/api/users` | POST | CSRF 検証、access Cookie を Bearer に変換、BFF admin check、backend `/users` へ proxy | Backend `POST /users` は現状認証なし作成可能。BFF 削除で権限が緩むため、admin only にするか別 register endpoint に分離するか Task 0-2 で決定する。 |
| `/api/users/me` | GET | access Cookie を Bearer に変換し `/users/me` へ proxy | FastAPI `/users/me` が Cookie 認証 current user に対応する。 |
| `/api/users/me` | PUT | CSRF 検証、access Cookie を Bearer に変換し `/users/me` へ proxy | FastAPI `/users/me` が Cookie 認証と CSRF 検証に対応する。 |
| `/api/users/[id]` | GET | access Cookie を Bearer に変換、BFF admin check、backend `/users/{id}` へ proxy | Backend 側の `read:users` permission と BFF admin check の parity を Task 0-2 で確認する。 |
| `/api/users/[id]` | PUT | CSRF 検証、access Cookie を Bearer に変換、BFF admin check、backend `/users/{id}` へ proxy | Backend 側の `update:users` permission と BFF admin check の parity を Task 0-2 で確認する。 |
| `/api/users/[id]` | DELETE | CSRF 検証、access Cookie を Bearer に変換、BFF admin check、backend `/users/{id}` へ proxy | Backend 側の `delete:users` permission と BFF admin check の parity を Task 0-2 で確認する。 |
| `/api/sso/authorization` | GET | redirect_uri を backend `/auth/sso/authorization` へ proxy、cookie 転送 | SPA が backend `/auth/sso/authorization` を直接呼ぶ。CORS / credentials 方針は Task 0-2 で決定する。 |
| `/api/sso/login` | POST | CSRF 検証、backend `/auth/sso/login` へ exchange proxy、返却 token で Cookie 発行、`/auth/me` 取得、redirect 用 response shaping、CSRF rotate | FastAPI が SSO exchange、Cookie 発行、CSRF 要否、response shape を担う。token value を body に返すかは Task 0-2 で決定する。 |
| `/api/saml/authorization` | GET | redirect_uri 必須検証、backend `/auth/saml/authorization` へ proxy、cookie 転送 | SPA が backend `/auth/saml/authorization` を直接呼ぶ。redirect_uri 要件は backend contract に寄せる。 |
| `/api/saml/login` | POST | CSRF 検証、Origin check、login_ticket / relay_state 必須検証、backend `/auth/saml/login` へ exchange proxy、Cookie 発行、backend Set-Cookie forwarding、redirect 用 response shaping | FastAPI が SAML ticket exchange、Cookie 発行、CSRF / Origin 要否、response shape を担う。代替防御は Task 0-2 で決定する。 |
| `/api/health` | GET | frontend health response | Vite SPA では静的配信 healthcheck、backend healthcheck、または container healthcheck に置換する。Task 3-2 で決定する。 |

注: file 数は 16 件だが、複数 method を持つ route は method 別に分類した。

### UI 移植対象

| 現行ファイル / 領域 | 移植方針 |
| --- | --- |
| `frontend/src/app/page.tsx` | React Router の public home route へ移植。`next/navigation` と `next/link` を置換する。footer の Next.js 表記は削除する。 |
| `frontend/src/app/auth/login/page.tsx` / `components/auth/login-form.tsx` | React route + form component として移植。submit 先は FastAPI browser login contract に合わせる。 |
| `frontend/src/app/auth/register/page.tsx` / `components/auth/register-form.tsx` | React route + form component として移植。register 後の遷移は Task 0-2 contract に合わせる。 |
| `frontend/src/app/dashboard/**` / `components/layout/dashboard-layout.tsx` | React Router nested routes へ移植。`Link`、`useRouter`、`usePathname` を React Router に置換する。 |
| `frontend/src/app/sso/callback/page.tsx` | React Router callback route へ移植。`useSearchParams` と navigation を React Router に置換し、backend SSO cookie endpoint を直接呼ぶ。 |
| `frontend/src/app/auth/saml/callback/page.tsx` | React Router callback route へ移植。CSRF bootstrap と SAML login endpoint は backend contract に合わせる。 |
| `frontend/src/app/layout.tsx` / `globals.css` | Vite `main.tsx` / app root / CSS import へ移植。`next/font/google` は削除または CSS / font package に置換する。 |
| `frontend/src/components/ui/**`, `components/auth/**`, `components/layout/**`, `hooks/**`, `stores/**`, `types/**` | Next.js import を含まないものは原則再利用する。Next.js navigation/link 依存だけ置換する。 |

### Next.js 依存 API 置換表

| Next.js 依存 | 使用箇所 | React SPA 置換 |
| --- | --- | --- |
| `next/server` `NextRequest` / `NextResponse` | `frontend/src/app/api/**`, `frontend/src/middleware.ts`, `lib/cookie-utils.ts`, `lib/csrf-utils.ts` | 削除。BFF server behavior は FastAPI へ移管する。SPA 側は `fetch` と browser APIs のみ使う。 |
| `next/navigation` `useRouter` | home、login/register form、auth guard、dashboard layout、SSO/SAML callback | React Router の `useNavigate` に置換する。 |
| `next/navigation` `usePathname` | auth guard、dashboard layout | React Router の `useLocation` に置換する。 |
| `next/navigation` `useSearchParams` | SSO/SAML callback | React Router の `useSearchParams` に置換する。 |
| `next/link` | home、login/register form、dashboard layout | React Router の `Link` / `NavLink` に置換する。 |
| `next/font/google` | `frontend/src/app/layout.tsx` | CSS import、system font、または Vite 対応 font 読み込みへ置換する。 |
| Next middleware protected route | `frontend/src/middleware.ts` | Client-side auth guard と backend 401 handling に置換する。security boundary は backend auth dependency に置く。 |
| Next API route proxy | `frontend/src/app/api/**` | SPA API client が FastAPI を `credentials: "include"` で直接呼ぶ。 |

### Browser storage 利用

| Storage | 使用箇所 | 内容 | 移行判断 |
| --- | --- | --- | --- |
| `sessionStorage` | `lib/sso-storage.ts` | OIDC `state`, `nonce`, PKCE `codeVerifier`, `redirectUri`, expiry | token ではなく公開可能な flow correlation data。React SPA でも維持可能。 |
| `sessionStorage` | `lib/saml-storage.ts` | SAML `relayState`, `redirectUri`, expiry | token ではなく flow correlation data。React SPA でも維持可能。 |
| `localStorage` | `lib/saml-storage.ts` | SAML context backup | Safari 等で sessionStorage が失われる場合の fallback。保持期限、削除、機密性を Task 0-2 / Task 2-4 で確認する。token は保存しない。 |
| `document.cookie` | `lib/cookie-api-client.ts`, `app/auth/saml/callback/page.tsx` | JS-readable CSRF token 読み取り | backend CSRF transport 方針に合わせて維持または response body bootstrap に置換する。auth Cookie は `HttpOnly` のため読まない。 |

### Backend parity が必要な処理

- access token / refresh token Cookie 発行と clear
- CSRF token 生成、bootstrap、検証、rotate
- Cookie 認証からの current user 解決
- Cookie 認証された state-changing request の CSRF 検証
- Bearer-token client には CSRF を要求しない互換性
- refresh token を Cookie から読む contract
- refresh 失敗時の Cookie clear
- logout 時の Cookie clear と必要な refresh token 失効
- SSO authorization init の direct browser contract
- SSO login exchange 後の Cookie 発行と token body 非公開方針
- SAML authorization init の direct browser contract
- SAML login ticket exchange 後の Cookie 発行、Origin / CSRF / RelayState / ticket 検証
- Users API の BFF admin check parity
- frontend healthcheck の Next.js 非依存化

### BFF authorization parity 表

| Route | BFF 側 check | 現行 backend 側 check | 移管後の期待 policy |
| --- | --- | --- | --- |
| `/api/todos` GET/POST | access Cookie 必須。POST は CSRF 必須。 | `/todos` は `ActiveUserDep` 必須。POST は backend CSRF なし。 | Cookie auth current user 対応。Cookie 認証 POST は CSRF 必須。Bearer client は既存どおり CSRF なしで可。 |
| `/api/todos/[id]` GET/PUT/DELETE | access Cookie 必須。PUT/DELETE は CSRF 必須。 | `/todos/{id}` は `ActiveUserDep` 必須。owner check あり。PUT/DELETE は backend CSRF なし。 | Cookie auth current user 対応。Cookie 認証 PUT/DELETE は CSRF 必須。owner check 維持。 |
| `/api/users` GET | access Cookie 必須。BFF で `is_superuser` または role `admin` 必須。 | `/users` は `read:users` permission 必須。 | `read:users` と BFF admin check が同等か確認。不一致なら Task 0-2 で backend policy を決定する。 |
| `/api/users` POST | access Cookie 必須。BFF で admin 必須。CSRF 必須。 | `/users` は現状認証なし作成可能。 | BFF 削除で権限が緩む最大リスク。admin user creation と public registration を分離するか、`POST /users` の policy を変更する。 |
| `/api/users/me` GET/PUT | access Cookie 必須。PUT は CSRF 必須。 | `/users/me` は `ActiveUserDep` 必須。PUT は backend CSRF なし。 | Cookie auth current user 対応。Cookie 認証 PUT は CSRF 必須。 |
| `/api/users/[id]` GET | access Cookie 必須。BFF で admin 必須。 | `/users/{id}` は `read:users` permission 必須。 | `read:users` と admin check の parity を確認する。 |
| `/api/users/[id]` PUT | access Cookie 必須。BFF で admin 必須。CSRF 必須。 | `/users/{id}` は `update:users` permission 必須。`is_superuser` 変更は superuser のみ。 | Permission policy と admin check の parity を確認。Cookie 認証 PUT は CSRF 必須。 |
| `/api/users/[id]` DELETE | access Cookie 必須。BFF で admin 必須。CSRF 必須。 | `/users/{id}` は `delete:users` permission 必須。self-delete は拒否。 | Permission policy と admin check の parity を確認。Cookie 認証 DELETE は CSRF 必須。 |
| `/api/auth/*` state-changing | login/register/refresh/logout は CSRF 必須。 | backend は Bearer / token body contract 中心で CSRF なし。 | browser Cookie endpoint では CSRF 必須。既存 Bearer / token body client は互換維持するか明示的に破壊する。 |
| `/api/sso/login` | CSRF 必須。state/nonce/PKCE は backend service が検証。 | backend `/auth/sso/login` は state/nonce/PKCE 検証、token body response。CSRF なし。 | Cookie endpoint の CSRF 要否を Task 0-2 で決める。除外する場合は代替防御を明記する。 |
| `/api/saml/login` | CSRF 必須。Origin check。ticket / RelayState 必須。 | backend `/auth/saml/login` は ticket / RelayState 検証、token body response。CSRF / Origin check は BFF 側。 | Cookie endpoint の CSRF / Origin 要否を Task 0-2 で決める。 |

### 確認結果

- API route handler 16 件はすべて分類した。
- Cookie / CSRF / refresh / SSO / SAML の移管先は Task 0-2 で contract 化できる粒度まで整理した。
- BFF 削除で権限が緩む route は `/api/users` POST が最重要。`/api/users*` の admin check と backend permission policy の parity も Task 0-2 の必須確認事項とする。
