# フロントエンド実装 点検メモ（Codex）

## 目的

`frontend/` の Vite + React SPA を、今後の業務システム UI 基盤として拡張する前提で点検した結果を記録する。

既存の `docs/dev/frontend-implementation-review-findings.ja.md` は Cline が作成中と思われる未追跡ファイルであるため、本メモでは上書きせず、Codex 側の独立した確認結果として整理する。

## 確認した公式・一次情報

- React 公式: コンポーネントと Hooks は pure であること、Effect は目的別に分離すること、再利用する stateful logic は具体的な Custom Hook に切り出すこと。
- TanStack Query v5 公式: Query は server state 管理であり、queryFn はデータを返すかエラーを throw すること。mutation 後は invalidate / optimistic update を設計的に使い分けること。
- React Router v7 公式: `BrowserRouter` + `Routes` の Declarative Mode は有効。ただし route-level data loading / pending / action を活用したい場合は `createBrowserRouter` + `RouterProvider` の Data Mode が選択肢になる。

## 現状評価

現状の frontend は、Vite SPA としてのビルド・型チェックは成立している。FastAPI バックエンドに `credentials: "include"` で直接接続し、実トークンをフロントに保持しない Cookie session / CSRF 境界を採っている点は維持すべきである。

一方で、実装の形はまだ「Next.js から Vite SPA へ移行した参照 Todo アプリ」に近い。業務画面を増やす前に、ルーティング、API クライアント、Query、通知、テスト、CI の基盤を先に固めるべき状態である。

## 優先修正ポイント

### C-01: API クライアントと TanStack Query のエラー境界を統一する

`frontend/src/lib/react-query.tsx` の retry 判定は `axios` エラーを前提にしているが、実通信は `frontend/src/lib/cookie-api-client.ts` の `fetch` で行われている。このため、4xx は retry しないという意図がグローバル設定では機能しない。

対応方針:

- `axios` を使わないなら依存と `isAxiosError` 判定を削除する。
- `fetch` レイヤーで `ApiError` クラスまたは discriminated union を定義し、`status` / `code` / `message` を正規化する。
- Query hooks は `Response` を直接扱わず、型付きデータを返す API 関数だけを呼ぶ。
- TanStack Query の retry は正規化済みエラーの `status` で判定する。

### C-02: `cookie-api-client.ts` を transport と domain API に分割する

現状は CSRF 初期化、Cookie 付き fetch、auth / sso / saml / todo / user API が 1 ファイルに集約されている。業務機能が増えると肥大化が確実である。

推奨構成:

- `src/shared/api/http-client.ts`: baseUrl、credentials、CSRF、JSON parse、ApiError 正規化
- `src/features/auth/api.ts`: auth / session / me
- `src/features/sso/api.ts`: SSO flow
- `src/features/saml/api.ts`: SAML flow
- `src/features/tasks/api.ts`: todo/task endpoints
- `src/features/*/queries.ts`: query keys と hooks

### C-03: ルーティング方針を明文化し、Next.js 由来の構造を整理する

`src/app/**/page.tsx`、`'use client'`、`src/app/api/**`、ルートの `.next/` など、Next.js App Router の語彙が残っている。実際は Vite + React Router なので、新規参画者が構造を誤解しやすい。

当面は React Router Declarative Mode のままでもよい。ただし業務画面の増加に備え、少なくとも route 定義を `src/routes.tsx` に分離し、画面単位の lazy loading を導入する。認証済み layout route も `DashboardLayout` の手動ラップではなく、ルート構造側で表現する。

Data Router へ移行する場合は、loader/action と TanStack Query の責務が重複しないように決める。API server state の主体は TanStack Query に寄せ、Router は navigation / layout / route error boundary を主責務にするのがこのプロジェクトでは扱いやすい。

### C-04: 通知実装を sonner に一本化する

`useUIStore().addNotification()` は各所から呼ばれているが、`Toaster` は Zustand の `notifications` を購読せず、`sonner` の `toast()` 呼び出しもない。現状では操作結果がユーザーに表示されない。

対応方針:

- 単純化するなら Zustand の `notifications` を削除し、呼び出し側を `toast.success/error` に置換する。
- 通知履歴が必要なら `addNotification()` 内で `toast()` を発火し、履歴保存と表示を明示的に分ける。

### C-05: ESLint / テスト / CI を基盤化する

`npm run lint` は成功するが、`eslint.config.mjs` は ignore だけで実効ルールがない。フロントエンドの自動テストもなく、CI に frontend job もない。

最低ライン:

- ESLint: TypeScript、React Hooks、React Refresh、アクセシビリティ系ルールを有効化する。
- Unit / component: Vitest + Testing Library。
- API 境界: MSW で auth / csrf / task の正常系・401・403 CSRF retry を検証する。
- E2E: Playwright で login、protected route、task CRUD の代表フローを検証する。
- CI: `npm ci`、`npm run check-types`、`npm run lint`、`npm run build`、`npm test` を frontend job として追加する。

### C-06: 業務画面拡張前に server state と client state の線引きを固定する

TanStack Query は server state、Zustand は local/client state に限定する方針でよい。現在の Zustand は UI 状態中心であり、この境界は妥当である。

追加ルール:

- API 由来データは Zustand に入れない。
- query key は feature 単位で factory を持つ。
- staleTime はドメイン別に理由を持って定義する。
- mutation 後の反映は invalidate / setQueryData / optimistic update のどれを使うか、操作単位で決める。

### C-07: ハードコードされたダッシュボードと未実装導線を整理する

`dashboard/page.tsx` の統計値と recent tasks は固定値であり、業務画面基盤としては危険である。`dashboard-layout.tsx` には `/dashboard/profile` など未定義ルートへの導線もある。

対応方針:

- モック表示で残すなら明示的に `mock` データとして隔離する。
- 実画面として残すなら backend API と query hook を用意する。
- 未実装ルートは非表示にするか、Not Implemented 画面を正式に定義する。

### C-08: ビルド出力を分割する

承認後に `npm run build` は成功したが、Vite が `assets/index-*.js` 602KB の chunk size warning を出している。今後画面が増える前に route-level lazy loading を導入するべきである。

対応方針:

- route component を `lazy()` / dynamic import に分割する。
- 重い UI/フォーム/日付処理ライブラリは画面単位に遅延ロードする。
- 必要なら `rollupOptions.output.manualChunks` を設定する。

## 検証結果

- `npm run check-types`: 成功
- `npm run lint`: 成功。ただし ESLint 実効ルール未設定のため品質担保としては不十分
- `npm run build`: サンドボックス内では esbuild spawn が `EPERM`。承認後の通常実行では成功。Vite chunk size warning あり

## 推奨する刷新順序

1. 通知不具合、fetch / ApiError / retry 判定、console 出力を修正する。
2. ESLint と frontend CI を有効化する。
3. API クライアントを transport + feature API + query hooks に分割する。
4. ルーティング構成を `routes.tsx` に集約し、layout route と lazy loading を導入する。
5. Vitest / Testing Library / MSW で auth、CSRF、task query/mutation を固める。
6. Playwright で代表業務フローを追加する。
7. 上記を前提に、正式な「フロントエンド実装指針ガイド」を作成する。

