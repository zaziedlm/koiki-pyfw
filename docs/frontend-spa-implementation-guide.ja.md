# Frontend SPA Implementation Guide

最終更新: 2026-07-09

このガイドは、`frontend/` の Vite + React SPA を今後の業務 UI 実装の土台として使うための実装指針である。

旧 Next.js / App Router / BFF 前提の実装ガイドは現行構造とは一致しない。現行 frontend では Next.js runtime、`src/app/`、Route Handlers、`'use client'`、axios は使わない。

## 現行前提

- frontend は Vite + React + TypeScript の browser SPA である。
- routing は React Router を使い、route 定義は `frontend/src/routes/` に集約する。
- backend API は FastAPI を直接呼び、`credentials: "include"` を付ける。
- login / logout / session / refresh / CSRF / SSO / SAML の source of truth は backend である。
- frontend は access token / refresh token を browser storage に保存しない。
- Cookie session と CSRF 検証は backend contract に従う。
- server state は TanStack Query、client-only state は Zustand に分ける。

## Directory Guide

現行の主な配置は次の通り。

```text
frontend/src/
  App.tsx
  main.tsx
  routes/
  shared/api/
  features/
    auth/
    saml/
    sso/
    tasks/
    users/
  components/
    auth/
    layout/
    tasks/
    ui/
  lib/
  stores/
  styles/
  test/
  types/
```

配置方針:

- `routes/`: route component と route composition。layout route と route-level lazy loading もここで扱う。
- `shared/api/`: HTTP transport、CSRF header、JSON parse、`ApiError` 正規化。
- `features/<feature>/api.ts`: feature API 関数。URL と request/response の境界を持つ。
- `features/<feature>/queries.ts`: query key factory、TanStack Query hooks、cache invalidation。
- `components/<domain>/`: domain UI component。form、dialog、list など。
- `components/ui/`: 汎用 UI primitive。業務ロジックを入れない。
- `lib/`: UI 非依存の小さな helper。provider factory などもここ。
- `stores/`: theme/sidebar/notification など client-only state。
- `test/`: Vitest / Testing Library / MSW の共通 setup と render helper。

## Adding A Route

新規画面を追加するときは、次の順に進める。

1. `frontend/src/routes/<area>/<page>.tsx` に route component を作る。
2. `frontend/src/routes/index.tsx` に `lazy()` import と `<Route>` を追加する。
3. 認証が必要な画面は既存の `/dashboard` layout route 配下に置くか、`ProtectedRoute` を使う。
4. navigation に導線を追加する場合は `components/layout/dashboard-layout.tsx` の `navigation` を更新する。
5. 未実装 route への導線を残す場合は、意図を task / guide / issue に記録する。

現在は React Router の declarative route 構成を使う。Data Router の loader/action は導入していない。server state は TanStack Query を主責務にする。

## Adding A Backend API Use

新しい backend endpoint を frontend から使う場合の標準形:

1. response / request 型を `types/` または feature-local type として定義する。
2. `features/<feature>/api.ts` に API 関数を追加する。
3. API 関数は `cookieApiClient.requestJson<T>()` を使う。
4. `features/<feature>/queries.ts` に query key と query/mutation hook を追加する。
5. state-changing request は `cookieApiClient` の CSRF 処理に乗せる。
6. component は API client を直接呼ばず、query/mutation hook を呼ぶ。

API boundary の責務:

- transport: `shared/api/http-client.ts`
- feature endpoint: `features/<feature>/api.ts`
- cache / retry / invalidation: `features/<feature>/queries.ts`
- UI event / form handling: `components/` または `routes/`

## Error And Retry

HTTP error は `ApiError` に正規化する。

`ApiError` は次を持つ。

- `status`
- `code`
- `message`
- `details`

TanStack Query の default retry は `lib/react-query-client.ts` で管理する。

- query: 400-499 は原則 retry しない。ただし 429 は retry 対象。
- mutation: 400-499 は retry しない。
- transient error は既定回数まで retry する。

UI で error を表示するときは、必要に応じて `isApiError()` で判定する。backend 由来の message をそのままユーザー表示するかは画面ごとに判断する。

## Forms, Validation, Mutation, Notification

現行の form pattern:

- form state: React Hook Form
- validation: Zod
- mutation: TanStack Query mutation hook
- notification: `useUIStore().addNotification`

標準 flow:

1. dialog / form component で Zod schema を定義する。
2. submit handler で feature mutation hook の `mutateAsync()` を呼ぶ。
3. 成功時は mutation hook 側で query invalidation / cache update を行う。
4. UI component は成功/失敗 toast と dialog close/reset を扱う。
5. API response を Zustand に保存しない。

notification 表示は `stores/ui-store.ts` が `sonner` へ集約している。message 文言は各 component から渡す。

## Auth, Cookie, CSRF

認証境界は backend が持つ。

frontend の役割:

- `/auth/session/*` endpoint を `credentials: "include"` で呼ぶ。
- state-changing request に CSRF header を付ける。
- `CSRF_TOKEN_INVALID` の 403 を受けた場合は CSRF token を更新し、1 回 retry する。
- protected UI は `AuthGuard` / `ProtectedRoute` で守る。

frontend がしないこと:

- access token / refresh token を localStorage/sessionStorage に保存する。
- Cookie 名や SameSite/Secure policy を frontend の source of truth にする。
- backend の auth/security 判定を UI state だけで代替する。

## Testing

テスト stack:

- Vitest
- Testing Library
- jest-dom
- jsdom
- MSW

共通 setup:

- `src/test/setup.ts`: jest-dom, MSW lifecycle, Testing Library cleanup
- `src/test/server.ts`: MSW server
- `src/test/render.tsx`: React Query provider と MemoryRouter provider

追加基準:

- `shared/api/`: error 正規化、CSRF retry、transport boundary を unit test する。
- `features/<feature>/queries.ts`: 代表 mutation と invalidation/caching risk を test する。
- `components/auth/`: guard、redirect、role fallback など auth-sensitive UI を component test する。
- form/dialog: validation と submit flow に regress risk がある場合に component test を追加する。

E2E:

- Playwright は未導入。
- login -> task CRUD -> logout の browser E2E は、dev/v0.8 で runtime flow が固定された後に別タスクで扱う。

## Validation Commands

frontend 変更時の標準確認:

```bash
npm ci
npm test
npm run check-types
npm run lint
npm run build
```

現行 lint は exit code 0 だが、UI helper export に対する `react-refresh/only-export-components` warning が残っている。これは開発時 Fast Refresh の warning であり、本番 build には影響しない。CI ログを clean にしたい場合は、UI helper の分離を別 cleanup として扱う。

Codex sandbox では `npm test` / `npm run build` が Vite/esbuild の `spawn EPERM` に当たる場合がある。その場合は通常権限で再実行して確認する。

## CI

frontend CI は現時点では有効化していない。

`dev/v0.8` で React SPA 版を正式対象にするときに、`.github/workflows/frontend-ci.dev-v0.8.yml.disabled` の内容を既存 `.github/workflows/ci.yml` へ移す。

有効化時の expected checks:

- `npm ci`
- `npm run check-types`
- `npm run lint`
- `npm test`
- `npm run build`

`.yml.disabled` は GitHub Actions の workflow 対象外なので、現時点では Actions を発火しない。

## Stale Docs

旧 Next.js 15 + BFF 前提の guide と audit は `docs/archive/frontend-nextjs-bff/` に保存している。現行 Vite + React SPA の実装手順としては使わない。

認証 API の backend contract を確認する場合は `docs/authentication-api-guide.md` を参照してよいが、frontend 実装例のうち Next Route Handlers / BFF / axios / localStorage 前提の記述は現行 frontend の実装方針ではない。

## Follow-up Candidates

- dev/v0.8 作成時に frontend CI を既存 `ci.yml` へ統合する。
- Playwright による login -> task CRUD -> logout E2E を追加する。
- `react-refresh/only-export-components` warning を消すため、UI helper export を別ファイルへ分離する。
- 旧 Next.js guide と audit は `docs/archive/frontend-nextjs-bff/` に保存済み。内容を現行実装の判断根拠としては使わない。
- `dashboard-layout.tsx` の navigation と `login-form.tsx` の `/auth/forgot-password` は、ダッシュボードUIレイアウトの参考配置例として残している。対応する route は未実装(意図的な保留)。実装するか、UIから外すかは今後のタスクで判断する。
