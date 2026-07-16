# Frontend Target Architecture

> **本書は Task 4-1 完了時点の初期計画案であり、現行の配置方針ではない。**
> 現行の配置方針は `docs/frontend-spa-implementation-guide.ja.md` を参照すること。
>
> 実装を進める過程で、より シンプルで迷わない実装を提供するために構成を見直した結果、本書の「目標構成」とは以下の点で異なる、より単純な構成が採用された。
>
> - `src/shared/config/`, `src/shared/ui/`, `src/shared/lib/` は分離せず、`src/shared/api/` のみを置く
> - feature 配下の `components/`・`types.ts` は採用せず、トップレベルの `src/components/<domain>/`・`src/types/` に統一する
> - `src/hooks/` は廃止し、`src/features/<feature>/queries.ts` に統合する
>
> 本書は初期検討時の設計意図を記録した参考資料として残す。現行実装との整合判断は常に `docs/frontend-spa-implementation-guide.ja.md` を優先すること。

## 目的

この文書は、`frontend/` を Vite + React SPA として保守・拡張するための配置方針と責務境界を固定する。

後続の refresh task では、本書を frontend 構成変更の判断基準として扱う。既存実装と矛盾する場合は、現行コードを確認した上で、小さい単位で本書の方向へ寄せる。

## 現状棚卸し

2026-07-09 時点の `frontend/src/` は次の構成である。

| 現在の場所 | 現在の責務 | 課題 |
|---|---|---|
| `src/App.tsx` | `BrowserRouter` / `Routes` による route composition | 画面追加の入口が単一ファイルに集中している |
| `src/main.tsx` | React root、React Query provider、Toaster、global CSS | bootstrapping と provider composition は妥当 |
| `src/routes/**` | 実際の route component と route composition | React Router の route entry として明確 |
| `src/components/auth/` | login / register / auth guard | feature UI と auth policy が混在している |
| `src/components/layout/` | dashboard shell と navigation | route 定義と navigation 定義が分離していない |
| `src/components/tasks/` | task list / create / edit / delete UI | task feature として独立可能 |
| `src/components/ui/` | shadcn/ui primitives と Toaster wrapper | shared UI として維持する |
| `src/hooks/` | auth / todo / sso / saml query hooks | feature 境界が hooks 名だけに依存している |
| `src/lib/` | config、React Query、Cookie API client、PKCE、SSO/SAML storage | transport、feature API、config、small utility が混在している |
| `src/stores/` | Zustand UI store | UI state 中心で妥当。ただし通知表示との接続が未整理 |
| `src/types/` | API / auth / todo / security / user 型 | backend schema と frontend view model の区別が弱い |

## 目標構成

新規実装と移動後の構成は次を標準にする。

| 目標の場所 | 責務 |
|---|---|
| `src/main.tsx` | DOM root、global provider composition、global CSS import |
| `src/App.tsx` | SPA root component。`src/routes` の route composition を呼び出す |
| `src/routes/` | route 定義、layout route、route-level lazy loading、route error boundary |
| `src/shared/api/` | HTTP transport、`credentials: "include"`、CSRF header、JSON parse、`ApiError` 正規化 |
| `src/shared/config/` | `VITE_*` public config の読み取りと validation |
| `src/shared/ui/` | feature に依存しない UI primitives / shadcn/ui wrappers |
| `src/shared/lib/` | UI 非依存の小さな共通関数 |
| `src/features/<feature>/api.ts` | feature ごとの backend API 関数 |
| `src/features/<feature>/queries.ts` | query keys、query hooks、mutation hooks |
| `src/features/<feature>/components/` | feature 専用 UI component |
| `src/features/<feature>/types.ts` | feature 専用型。backend schema と view model は必要に応じて分ける |
| `src/stores/` | server state ではない client-only state |

Task 2-2 で `src/app/**/page.tsx` と `src/app/api/**` は削除済みである。route component は `src/routes/` 配下へ置き、Next.js server runtime、Route Handler、App Router conventions は frontend 内に置かない。

## 互換入口を残さない方針

この frontend refresh では、旧配置を温存するための compatibility wrapper、互換 re-export、legacy import alias を原則として追加しない。

- ファイル移動時は呼び出し側 import を新しい責務境界へ更新する
- 旧 `src/hooks/*` や旧 `src/lib/cookie-api-client.ts` のような入口は、利用元を移した時点で削除する
- 移行中の一時 wrapper が必要になった場合でも、同じタスク内で削除まで完了させる
- 下位互換のためだけの barrel export は作らない
- 例外は外部公開 API として維持が必要な場合に限り、理由と削除条件をタスクの `実施結果` に明記する

この方針は frontend 内の刷新対象に適用する。repository root の `app/` が backend legacy import compatibility を担うという既存 backend 境界とは別の話として扱う。

## Router 方針

当面は React Router の Declarative / Library Mode を継続する。

理由:

- 現行実装は `BrowserRouter`、`Routes`、`Route`、`Navigate` による SPA routing で成立している
- API server state は TanStack Query を主体にするため、Data Router の loader/action を急いで導入すると責務重複が起きやすい
- 先に route 定義の集約、layout route、lazy loading、error boundary を整える方が移行リスクが小さい

Data Router を導入する場合の条件:

- route-level pending / error / redirect が明確な価値を持つ
- loader/action と TanStack Query の責務分担を route 単位で説明できる
- auth / csrf / sso / saml の backend ownership を崩さない

## TanStack Query と Router の境界

TanStack Query が server state の主責務を持つ。

- API 由来データの取得、cache、retry、invalidation、mutation 後反映は TanStack Query で扱う
- Router は URL、navigation、layout、route matching、not found / route error 表示を扱う
- Router loader は、画面表示前に必ず必要な軽量な route metadata か、redirect 判断に限定して検討する
- Router action は、フォーム送信を route contract として強く扱う必要が出るまで導入しない
- Query hook は raw `Response` を返さず、feature API 関数が返した型付きデータか `ApiError` を扱う

## Zustand 境界

Zustand に保持してよい state:

- sidebar open / collapsed などの UI preference
- theme などの client-only preference
- modal、drawer、command palette など、URL や server state に載せない一時 UI state
- 表示履歴として明示的に必要な通知履歴

Zustand に保持してはいけない state:

- access token / refresh token / id token
- CSRF token の source of truth
- user profile、roles、permissions など backend API 由来の server state
- task list、dashboard stats など backend API 由来の業務データ
- SSO / SAML の長寿命 session 情報

SSO PKCE verifier、OIDC state / nonce、SAML RelayState などの一時的な flow correlation data は、専用 storage helper で扱い、Zustand の永続 store へ入れない。

## API 境界

HTTP 呼び出しは次の順で流す。

1. UI component が `useXxxQuery` / `useXxxMutation` を呼ぶ
2. Query hook が feature API 関数を呼ぶ
3. Feature API 関数が `shared/api` の transport を呼ぶ
4. Transport が base URL、Cookie credentials、CSRF、JSON parse、error normalization を担う

`shared/api` は少なくとも次を提供する。

- `ApiError`: `status`, `message`, `code`, `details` を持つ error
- JSON response parser
- empty response handling
- CSRF invalid response 時の最大 1 回 retry
- 4xx / 5xx / network failure の正規化

`axios` を使わない限り、retry 判定や error handling で axios 固有 API に依存しない。

## 移行順序

後続タスクは次の順序で進める。

1. Task 0-2 で React / React DOM / TanStack Query / React Router の version baseline を確定する
2. Task 1-1 で通知を sonner 表示へ接続し、本番不要な console 出力を整理する
3. Task 1-2 で `ApiError` と fetch transport の error / retry 境界を整える
4. Task 2-1 で transport、feature API、query hooks を分割する
5. Task 2-2 で route 定義を `src/routes/` へ集約し、Next.js 由来の命名と残骸を整理する
6. Task 2-3 で dashboard の mock / real data 境界と navigation を整理する
7. Task 3-1 で ESLint と frontend CI を実効化する
8. Task 3-2 で Vitest / Testing Library / MSW の最小テスト基盤を入れる
9. Task 4-1 で実装ガイドへ反映し、最終検証を行う

Task 2-1 と Task 2-2 は import 移動が競合しやすいため、同時に進める場合は `routes` と `features` の移動単位を明確に分ける。

## 維持する認証境界

刷新中も次の境界は変更しない。

- backend が Cookie 発行、token refresh、logout、CSRF 検証、SSO token exchange、SAML ticket exchange を管理する
- frontend は access token / refresh token を browser storage に保存しない
- frontend は backend API を `credentials: "include"` 付きで直接呼び出す
- frontend の `VITE_*` は public browser config として扱う
- Cookie 名、Cookie 属性、CSRF header / cookie contract の source of truth は backend に置く
