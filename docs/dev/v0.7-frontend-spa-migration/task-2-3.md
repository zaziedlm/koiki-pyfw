# Task 2-3: route / page migration

## 目的

Next.js App Router の pages を React Router ベースの SPA route に移行する。

## 事前条件

- Task 2-2 が完了している

## 対象 route

- `/`
- `/auth/login`
- `/auth/register`
- `/dashboard`
- `/dashboard/tasks`
- `/sso/callback`
- `/auth/saml/callback`

## 実施手順

1. `react-router-dom` を導入する
2. route table を作成する
3. `next/link` を `Link` from `react-router-dom` に置き換える
4. `next/navigation` を `useNavigate` / `useLocation` に置き換える
5. `AuthGuard`, `ProtectedRoute`, `PublicRoute` を React Router 前提にする
6. dashboard と tasks 画面を移植する
7. landing page の Next.js 文言を削除する

## 検証

- 未ログインで protected route へ入ると login へ遷移する
- ログイン済みで public route へ入ると dashboard へ遷移する
- route refresh しても SPA fallback で表示できる

## 完了条件

- 主要画面が React Router 上で動作する

## 実施結果

実施済み。

- `react-router-dom` を追加した。
- `frontend/src/App.tsx` に React Router の route table を作成し、対象 route を SPA route として登録した。
- Home / login / register / dashboard / tasks / SSO callback / SAML callback を React Router 上で表示するようにした。
- 主要 browser component の `next/link` を `Link` from `react-router-dom` に置き換えた。
- 主要 browser component の `next/navigation` を `useNavigate` / `useLocation` / `useSearchParams` に置き換えた。
- `AuthGuard` / `ProtectedRoute` / `PublicRoute` を React Router 前提に変更した。
- landing page footer の Next.js 文言を削除した。

検証:

- `npm run check-types`
- `npm run build`
- Vite dev server: `http://localhost:3000/`
- SPA fallback HTTP 200:
  - `/`
  - `/auth/login`
  - `/dashboard`
  - `/dashboard/tasks`
  - `/sso/callback`
  - `/auth/saml/callback`
- `rg "next/link|next/navigation|useRouter|usePathname" frontend/src --glob '!app/api/**'`

補足:

- Next.js API route / middleware / server utility の Next 依存は Task 3-1 まで残す。
- 未ログイン / ログイン済み redirect の実ブラウザ確認は backend auth 状態に依存するため、ここでは route 実装と build / SPA fallback を確認した。
