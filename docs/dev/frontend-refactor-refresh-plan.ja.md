# Frontend React SPA Refactor / Refresh Plan

## 目的

この文書は、`frontend/` の Vite + React SPA を、今後の業務システム UI 実装の土台として使える状態へ刷新するための改修計画である。

対象は、React 公式、TanStack Query v5、React Router v7 の現行方針に沿って、現状の参照 Todo アプリ実装を次の状態へ近づけることとする。

- server state / client state の境界が明確である
- API 呼び出し、エラー処理、CSRF、Query retry が一貫している
- ルーティング、レイアウト、feature 配置が React SPA として説明可能である
- Next.js 移行残骸が新規実装者を混乱させない
- Lint、型チェック、テスト、CI が業務 UI の変更を継続的に検証できる
- 後続のフロントエンド実装指針ガイドの前提として使える

## Version Baseline

刷新開始時点では、次を目標 baseline として扱う。

- React: `19.2.7` 以上
- React DOM: `19.2.7` 以上
- TanStack Query: `5.101.2` 以上の v5 系
- React Router: `react-router-dom@7.18.1`

2026-07-09 時点の npm metadata では、`react-router` の latest は `8.2.0`、`react-router-dom` の latest は `7.18.1` である。また `react-router@8.2.0` は peer dependency として `react >=19.2.7` / `react-dom >=19.2.7` を要求する。

Task 0-2 で確認した結果、React Router v8 への移行は保留する。v8 では `react-router-dom` re-export package がなくなり、`react-router` / `react-router/dom` への import 移行が必要であることは確認済みだが、`react-router@8.2.0` は Node `>=22.22.0` を要求し、現行検証環境の Node `22.20.0` と CI Node baseline 未定義の状態では時期尚早と判断した。

このため、Task 2-2 は `react-router-dom@7.18.1` の Library Mode / Declarative Mode を前提に route 構成を整理する。

## 前提

既存の SPA 移行で決定した以下の認証境界は維持する。

- `frontend/` は Vite + React + TypeScript の browser SPA である
- browser routing は React Router が担う
- 認証 Cookie、CSRF 検証、token refresh、logout、SSO token exchange、SAML ticket exchange は FastAPI が担う
- SPA は access token / refresh token を browser storage に保存しない
- SPA は backend API を `credentials: "include"` 付きで直接呼び出す
- Cookie 認証された state-changing request では CSRF header を送る

この刷新は frontend の構造・品質基盤を整える作業であり、backend 認証 contract の再設計や新しい業務機能追加は主目的にしない。

## 現状の主要課題

点検結果は次を参照する。

- `docs/dev/frontend-implementation-review-findings.ja.md`
- `docs/dev/frontend-implementation-review-findings-codex.ja.md`

優先して扱う課題:

- `fetch` 実装に対し、TanStack Query retry 判定が `axios` 前提になっている
- API client が CSRF transport と feature API を 1 ファイルに抱え込んでいる
- Query hooks が `Response` parse と domain 型変換を直接持っている
- `sonner` 通知が実際には表示されない
- `src/app/**/page.tsx`、`'use client'`、`src/app/api/**`、`.next/` など Next.js 由来の語彙が残っている
- `eslint.config.mjs` に実効ルールがない
- frontend test stack と CI job がない
- dashboard の固定値、未定義 route 導線、production bundle の chunk size warning が残っている

## 目標アーキテクチャ

詳細な配置方針と責務境界は `docs/dev/frontend-target-architecture.ja.md` を参照する。

### 配置方針

React SPA として、次の責務分割を標準にする。

- `src/app/`: SPA の bootstrapping、provider composition、route composition。Next.js App Router の意味では使わない
- `src/routes/`: route 定義、layout route、route-level lazy loading
- `src/shared/api/`: HTTP transport、CSRF、API error 正規化
- `src/shared/config/`: `VITE_*` public config の読み取りと validation
- `src/shared/ui/`: 汎用 UI primitives / shadcn ui
- `src/shared/lib/`: UI 非依存の小さな共通関数
- `src/features/<feature>/`: feature ごとの API、query keys、query hooks、components、types
- `src/stores/`: server state ではない client-only state

既存コードを一度に完全移動する必要はないが、新規実装はこの方向へ寄せる。

### State 管理

- TanStack Query は server state のみを扱う
- Zustand は UI state、theme、sidebar、client-only transient state に限定する
- API response は Zustand に保持しない
- Query keys は feature ごとに factory を持つ
- staleTime / gcTime / retry は domain の性質に応じて理由を持って定義する

### API 境界

Query hook は `Response` を直接扱わない。

期待する呼び出し境界:

1. UI component が `useXxxQuery` / `useXxxMutation` を呼ぶ
2. Query hook が feature API 関数を呼ぶ
3. feature API 関数が `httpClient` を呼ぶ
4. `httpClient` が CSRF、credentials、JSON parse、error 正規化を担う

エラーは `ApiError` として `status`、`code`、`message`、任意の `details` を持つ形へ正規化する。TanStack Query の retry はこの `status` を見て判定する。

### Routing

当面は React Router の Library Mode を維持する。業務 SPA としては、Data Router へ移行するより先に、route 定義の集約、layout route、lazy loading、route error boundary を整える。

TanStack Query を server state の主責務にするため、React Router loader/action を導入する場合は、役割重複が起きない範囲に限定する。

### Testing

テストは次の層で整える。

- Unit: pure helper、ApiError 正規化、query key factory
- Component: form validation、guard、task list、dialog
- API integration in frontend: MSW による auth / csrf / task API の成功・失敗
- E2E: Playwright による login、protected route、task CRUD、logout

## 実行順序

詳細タスクは `docs/dev/frontend-refactor-refresh-tasks/` に置く。

1. `task-0-1.md` - frontend target architecture decision
2. `task-0-2.md` - React / TanStack / Router version baseline
3. `task-1-1.md` - notification and production log cleanup
4. `task-1-2.md` - fetch ApiError and TanStack Query retry alignment
5. `task-2-1.md` - API client and feature query split
6. `task-2-2.md` - routing and Next.js residue cleanup
7. `task-2-3.md` - dashboard and navigation data cleanup
8. `task-3-1.md` - ESLint and frontend CI baseline
9. `task-3-2.md` - frontend test baseline
10. `task-4-1.md` - implementation guide and final validation

## 完了条件

- `npm run check-types` が通る
- `npm run lint` が実効ルール付きで通る
- `npm run build` が通り、route-level lazy loading により初期 chunk warning が解消または明示的に判断済みである
- frontend unit / component tests が追加され、CI で実行される
- 少なくとも auth guard、CSRF retry、task mutation の代表フローがテストされている
- `frontend/` の構成が Vite + React SPA として説明でき、Next.js App Router と誤認させる構造が残っていない
- 改修結果を反映した frontend implementation guide が作成されている

## Change Control

この計画を変更する場合は、同じ change window で `docs/dev/frontend-refactor-refresh-tasks/` 配下のタスク指示書も更新する。
