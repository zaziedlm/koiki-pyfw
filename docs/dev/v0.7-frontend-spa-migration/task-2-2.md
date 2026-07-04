# Task 2-2: SPA API client / auth hooks

## 目的

Next.js route handler 経由の API client を、FastAPI 直呼びの Cookie 認証 client に置き換える。

## 事前条件

- Task 2-1 が完了している

## 対象

- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/hooks/use-cookie-auth-queries.ts`
- `frontend/src/hooks/use-cookie-todo-queries.ts`
- `frontend/src/hooks/use-sso-login.ts`
- `frontend/src/hooks/use-saml-login.ts`

## 実施手順

1. `NEXT_PUBLIC_*` を `VITE_*` に置き換える
2. API base URL 解決を Vite 前提にする
3. `credentials: "include"` を共通化する
4. CSRF bootstrap と header 付与を共通化する
5. login / register / refresh / logout / me を `/auth/session/*` backend contract に合わせる
6. Todo API を backend `/todos` 直呼びにする
7. SSO / SAML callback exchange を `/auth/session/sso/login` と `/auth/session/saml/login` に合わせる
8. token value を browser storage に保存していないことを確認する

## 検証

- 未ログイン時の `me` は null として扱える
- login 成功後に auth query が更新される
- Todo CRUD が Cookie 認証で呼び出される
- SPA client が Next.js `/api/*` route を呼んでいない
- SPA client が token value を response body から読まない

## 完了条件

- frontend API client が Next.js API route に依存していない

## 実施結果

実施済み。

- `frontend/src/lib/config.ts` の公開 env 解決を `VITE_*` 優先に変更し、既存 `NEXT_PUBLIC_*` は Next route handler 削除までの暫定 fallback とした。
- `frontend/src/lib/cookie-api-client.ts` を FastAPI backend base URL 直呼びに変更し、`credentials: "include"`、CSRF bootstrap、CSRF header 付与、CSRF 403 retry を共通化した。
- password auth の login / register / refresh / logout / me を `/auth/session/*` contract に合わせた。
- Todo API を backend `/todos` 直呼びに変更した。
- SSO / SAML の authorization と callback exchange を backend `/auth/sso/authorization`、`/auth/session/sso/login`、`/auth/saml/authorization`、`/auth/session/saml/login` に合わせた。
- login hook から旧 Next.js BFF response 前提の `new_cookie_set` 分岐と cookie propagation polling を削除した。
- `frontend/.env.local.example`、`frontend/.env.docker`、`frontend/.env.production.example` に `VITE_*` を追加した。

検証:

- `npm run check-types`
- `npm run build`
- Vite dev server: `http://localhost:3000/` / `http://127.0.0.1:3000` HTTP 200
- `rg "/api/(auth|sso|saml|todos)" frontend/src --glob '!app/api/**'`
- `rg "access_token|refresh_token" frontend/src/lib/cookie-api-client.ts frontend/src/hooks frontend/src/app/sso/callback/page.tsx frontend/src/app/auth/saml/callback/page.tsx`

補足:

- Next.js route handler 自体は Task 3-1 まで削除しない。
- SSO / SAML context の `sessionStorage` / `localStorage` 利用は state / nonce / relay state / code verifier 用であり、token value は保存しない。
