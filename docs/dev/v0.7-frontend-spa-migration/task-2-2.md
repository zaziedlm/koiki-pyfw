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
5. login / refresh / logout / me を backend contract に合わせる
6. Todo API を backend `/todos` 直呼びにする
7. token value を browser storage に保存していないことを確認する

## 検証

- 未ログイン時の `me` は null として扱える
- login 成功後に auth query が更新される
- Todo CRUD が Cookie 認証で呼び出される

## 完了条件

- frontend API client が Next.js API route に依存していない

## 実施結果

未実施。
