# Task 2-1: API client and feature query split

## 目的

肥大化した `cookie-api-client.ts` と hooks を、transport、feature API、query hooks に分割する。

## 事前条件

- Task 1-2 が完了している

## 対象

- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/hooks/use-cookie-auth-queries.ts`
- `frontend/src/hooks/use-cookie-todo-queries.ts`
- `frontend/src/hooks/use-sso-login.ts`
- `frontend/src/hooks/use-saml-login.ts`
- `frontend/src/types/`
- 新設する `frontend/src/shared/`、`frontend/src/features/`

## 実施手順

1. transport 層を `shared/api` へ移す
2. auth / sso / saml / tasks / users の API 関数を feature 単位へ分割する
3. query key factory を feature 単位へ分割する
4. query hooks と mutation hooks を feature 単位へ分割する
5. `types/` のうち backend schema と frontend-only view model を分ける
6. import path を更新する
7. 古い barrel export が曖昧な依存を作っていないか確認する

## 検証

- `npm run check-types`
- `npm run lint`
- `npm run build`
- login / me / task CRUD の手動確認、または MSW テスト

## 完了条件

- `cookie-api-client.ts` が全 feature API を抱え込んでいない
- feature ごとに API、query keys、query hooks の所在が明確である
- UI component が transport 詳細や raw `Response` を知らない

## 実施結果

未実施。

