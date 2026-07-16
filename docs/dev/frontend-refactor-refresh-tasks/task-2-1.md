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

完了。

- `frontend/src/shared/api/http-client.ts` を追加し、Cookie 付き fetch、CSRF bootstrap / header 付与、CSRF invalid 時の最大 1 回 retry、JSON parse、`ApiError` 正規化を transport 層へ移した。
- `frontend/src/shared/api/index.ts` を追加し、`ApiError`, `isApiError`, `CookieApiClient`, `cookieApiClient` を shared API の公開入口にした。
- feature API を次へ分割した。
  - `frontend/src/features/auth/api.ts`
  - `frontend/src/features/tasks/api.ts`
  - `frontend/src/features/sso/api.ts`
  - `frontend/src/features/saml/api.ts`
  - `frontend/src/features/users/api.ts`
- query key factory と query hooks を次へ分割した。
  - `frontend/src/features/auth/queries.ts`
  - `frontend/src/features/tasks/queries.ts`
- 旧 `frontend/src/hooks/use-cookie-auth-queries.ts`、`frontend/src/hooks/use-cookie-todo-queries.ts`、`frontend/src/hooks/use-sso-login.ts`、`frontend/src/hooks/use-saml-login.ts`、`frontend/src/hooks/index.ts` を削除し、互換 re-export は残さない方針にした。
- 旧 `frontend/src/lib/cookie-api-client.ts` を削除し、API client の入口を `shared/api` と `features/*/api.ts` に統一した。
- login / register / auth guard / dashboard layout / task components は feature query から import する形へ更新した。
- SSO / SAML authorization hooks と callback routes は feature API を使うようにし、raw `Response` parse を UI / hook 側から除去した。
- `types/` の本格的な backend schema / view model 分割は、現時点では既存 UI への影響が大きいため実施しなかった。feature API / query の所在を先に固定し、型の物理分割は後続の feature 整理で扱う。

検証結果:

- `rg "@/hooks|@/lib/cookie-api-client|use-cookie-auth-queries|use-cookie-todo-queries|use-sso-login|use-saml-login|cookieApiClient\\.(auth|sso|saml)|cookieApi\\.auth" frontend/src`: 該当なし
- `rg "response\\.ok|response\\.status|\\.json\\(\\)" frontend/src`: raw response handling は `shared/api/http-client.ts` に限定されていることを確認した
- `npm run check-types`: 成功
- `npm run lint`: 成功。ただし Task 3-1 前なので ESLint は実効ルール未整備
- `npm run build`: 通常権限で成功。initial JS chunk は 568.02 kB。500 kB 超過 warning は継続し、Task 2-2 の lazy loading で扱う

後続確認:

- backend / frontend コンテナ起動後に login と task create / update / delete を手動確認済み。
- app log で `POST /api/v1/todos` -> 201、`PUT /api/v1/todos/17` -> 200、`DELETE /api/v1/todos/17` -> 204 を確認済み。
