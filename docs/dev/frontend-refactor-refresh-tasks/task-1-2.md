# Task 1-2: fetch ApiError and TanStack Query retry alignment

## 目的

`fetch` ベースの API 呼び出しと TanStack Query の retry / error handling を一致させる。

## 事前条件

- Task 0-1 が完了している
- Task 1-1 が完了していることが望ましい

## 対象

- `frontend/src/lib/react-query.tsx`
- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/hooks/use-cookie-auth-queries.ts`
- `frontend/src/hooks/use-cookie-todo-queries.ts`
- `frontend/package.json`
- `frontend/package-lock.json`

## 実施手順

1. `axios` が実通信に使われていないことを確認する
2. `ApiError` を定義し、少なくとも `status`, `message`, `code`, `details` を扱えるようにする
3. `fetch` response の JSON parse と error shape 正規化を共通化する
4. CSRF invalid 時の 1 回 retry を transport 層に閉じ込める
5. Query hooks は `Response` を直接 parse せず、型付き API 関数の戻り値を受け取る形へ寄せる
6. `react-query.tsx` の retry 判定を `ApiError.status` ベースに変更する
7. 未使用になった `axios` 依存を削除する

## 検証

- `npm run check-types`
- `npm run lint`
- `npm run build`
- 401 / 403 / 422 / 429 / 500 の retry 方針を単体テストまたは MSW テストで確認する

## 完了条件

- `isAxiosError` に依存した retry 判定が残っていない
- Query hooks が `Response` を直接返さない
- 4xx retry 抑制が fetch 実装でも機能する
- CSRF invalid retry が最大 1 回に制限されている

## 実施結果

完了。

- `frontend/src/lib/cookie-api-client.ts` に `ApiError` を追加し、`status`, `message`, `code`, `details` を持つ error として正規化するようにした。
- `requestJson<T>()` を追加し、JSON parse、empty / 204 response handling、非 2xx response の `ApiError` 化を transport 側へ集約した。
- CSRF invalid response 時の refresh + retry は既存の `fetchWithCredentials()` に閉じ込めたまま、型付き API 関数から利用する形にした。retry は最大 1 回である。
- `cookieAuthApi` と typed な `cookieTodoApi` を追加し、auth / todo query hooks が raw `Response` を直接 parse しない形へ寄せた。
- `frontend/src/lib/react-query.tsx` の retry 判定を `isAxiosError` から `isApiError(error)` + `ApiError.status` ベースへ変更した。
- `axios` は実通信に使われていないことを確認し、`frontend/package.json` / `frontend/package-lock.json` から削除した。

検証結果:

- `rg "axios|isAxiosError|response\\.ok|response\\.status|\\.json\\(\\)" frontend/src/lib/react-query.tsx frontend/src/hooks/use-cookie-auth-queries.ts frontend/src/hooks/use-cookie-todo-queries.ts frontend/package.json frontend/package-lock.json`: 該当なし
- `npm run check-types`: 成功
- `npm run lint`: 成功。ただし Task 3-1 前なので ESLint は実効ルール未整備
- `npm run build`: 通常権限で成功。axios 削除後、initial JS chunk は 569.36 kB。500 kB 超過 warning は継続し、Task 2-2 の lazy loading で扱う

後続確認:

- Task 3-2 で `ApiError` 正規化、CSRF invalid retry、TanStack Query retry 判定の Vitest / MSW テストを追加した。
