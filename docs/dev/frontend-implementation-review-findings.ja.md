# フロントエンド実装 点検指摘事項

## 1. 目的

本ドキュメントは、`frontend/`（Vite + React SPA）の実装を対象に行った点検の結果を記録するものである。

**本ドキュメントのスコープは「点検・指摘事項の整理」までであり、コードの修正は含まない。** 発見した事項は、後続タスクで修正プランを立案する際の一次情報として、要約・簡略化せず可能な限り具体的（該当ファイル・該当箇所・事象・影響）に記載する。

対象は業務システムのフロントエンドUIの土台とすることを前提としており、公式ベストプラクティス（React / TanStack Query）との整合性、明確性を欠く実装（アンチパターン）の有無を中心に点検した。

## 2. 調査範囲・方法

- `frontend/src/` 配下のソースコード全体を対象に、ディレクトリ構成・エントリポイント・ルーティング・状態管理・APIクライアント・認証まわり・UIコンポーネントを個別に読解
- `frontend/package.json`、`vite.config.ts`、`tsconfig.json`、`eslint.config.mjs` 等の設定ファイルを確認
- `.github/workflows/ci.yml` を確認し、CIでのフロントエンド検証範囲を確認
- リポジトリ全体に対する正規表現検索により、テストファイル（`describe(`, `it(`, `vitest`, `@testing-library`）およびトースト通知呼び出し（`toast(`, `sonner`, `addNotification`）の有無・使用状況を確認
- `docs/dev/frontend-spa-migration-plan.ja.md`、`docs/dev/v0.7-frontend-spa-migration/task-4-1.md`、`docs/dev/frontend-review-antigravity.md` 等の移行時設計文書を確認し、意図された設計方針と現状実装の整合性を確認
- `docs/agent/testing.md` に記載されたプロジェクト全体のテスト方針を確認

なお `docs/FRONTEND_ENTERPRISE_AUDIT_ja.md` および `docs/frontend-application-development-guide.md` は、Next.js 15 App Router + BFF構成を前提とした旧世代のドキュメントであり、Vite SPAへの移行が完了した現状の実装を反映していない（`docs/dev/v0.7-frontend-spa-migration/task-4-1.md` にも「stale Next.js-era docs」として整理対象に記録されている）。本点検はこれら旧ドキュメントではなく、実際のソースコードを一次情報として実施した。

## 3. 現状のアーキテクチャ概要（点検の前提情報）

### 3.1 技術スタック

| 項目 | 内容 |
|---|---|
| ビルドツール | Vite 7.3.1 |
| フレームワーク | React 19 + TypeScript 5 |
| ルーティング | React Router v7（`BrowserRouter`、`App.tsx` にルート定義を集約） |
| サーバー状態管理 | TanStack Query v5（`@tanstack/react-query` ^5.83.0 + devtools） |
| クライアント状態管理 | Zustand v5（^5.0.6） |
| フォーム | react-hook-form + zod + `@hookform/resolvers` |
| UIコンポーネント | shadcn/ui（Radix UIプリミティブ）+ Tailwind CSS v4 |
| 通知 | sonner（依存関係としては存在するが実際には未結線。4.1節 F-01 参照） |
| HTTP通信 | `fetch`（`credentials: "include"`）を実際の通信手段として使用。`axios` ^1.16.0 は依存関係に存在するが実通信には未使用（4.2節 F-05 参照） |
| Lint | ESLint 9（ただし実効ルールは未設定。4.2節 F-04 参照） |

### 3.2 ディレクトリ構成の要点

- `frontend/src/app/**/page.tsx`：Next.js App Router時代の命名慣習が残存しているが、実際のルーティングは `App.tsx` の `BrowserRouter` が担っている（実体はNext.jsのRoute/Pageではない）
- `frontend/src/lib/`：`cookie-api-client.ts`（APIクライアント）、`config.ts`（環境変数集約）、`react-query.tsx`（QueryClientファクトリ）
- `frontend/src/hooks/`：`use-cookie-auth-queries.ts`、`use-cookie-todo-queries.ts`、`use-sso-login.ts`、`use-saml-login.ts`
- `frontend/src/stores/`：`ui-store.ts`（Zustand、UI状態専用）
- `frontend/src/components/`：`auth/`（認証ガード・フォーム）、`layout/`（アプリシェル）、`tasks/`（Todo機能UI）、`ui/`（shadcn/uiコンポーネント）

### 3.3 認証・セキュリティ境界の設計方針（概要）

`docs/dev/frontend-spa-migration-plan.ja.md` に基づき、以下の設計方針が採用されている。

- バックエンド（FastAPI）がアクセス/リフレッシュトークンの発行・ローテーション、httpOnly Cookie発行、CSRFトークン生成・検証、SSO認可コード交換、SAMLチケット交換、セキュリティログを一元管理する
- フロントエンドは実トークンを一切保持せず、PKCEの `code_verifier`、OIDCの `state`/`nonce`、SAMLの `RelayState` など、一時的かつ公開可能なフロー相関用データのみを `sessionStorage` に保持する
- Cookie属性は `HttpOnly`、本番環境で `Secure`、既定 `SameSite=Lax`、`Path=/`、可能な場合 `__Host-` プレフィックスを使用
- CSRFはダブルサブミット方式（Cookie: `koiki_csrf_token`、Header: `x-csrf-token`）。安全でないHTTPメソッドで必須、安全なGETおよび（現行契約上）Bearerトークンクライアントでは免除

この設計方針自体は妥当であり、点検時点で実装との齟齬は確認されなかった（5節「維持すべき良好な設計判断」参照）。

### 3.4 データ取得・状態管理の概要

- TanStack Queryの `QueryClient` は `frontend/src/lib/react-query.tsx` でファクトリ化され、`staleTime` 60秒、`gcTime` 10分、`refetchOnWindowFocus: false`、リトライロジックが設定されている（リトライロジックの不具合は4.2節 F-05 参照）
- Zustandストア（`ui-store.ts`）は `sidebarOpen`、`theme`、`notifications` を保持し、`persist` ミドルウェアと `partialize` により永続化対象を `{sidebarOpen, theme}` のみに限定している
- Query Key Factoryパターンとして `cookieAuthKeys`、`cookieTodoKeys` が部分的に導入されているが、命名規則・階層設計の規約化はされていない（4.4節 F-10 参照）

## 4. 点検で判明した問題点

各指摘事項にIDを付与する。今後の修正プラン立案時の参照キーとして使用すること。

### サマリ

| ID | 重要度 | 概要 | 該当ファイル |
|---|---|---|---|
| F-01 | 重大 | トースト通知（sonner）が実質機能していない | `components/ui/sonner.tsx`, `stores/ui-store.ts` |
| F-02 | 重大 | フロントエンドの自動テストが皆無 | リポジトリ全体 |
| F-03 | 重大 | CIパイプラインにフロントエンドジョブが存在しない | `.github/workflows/ci.yml` |
| F-04 | 高 | ESLintの実効ルールが未設定 | `eslint.config.mjs` |
| F-05 | 高 | TanStack Queryのリトライ抑制ロジックがaxios/fetch不一致で機能していない | `lib/react-query.tsx`, `lib/cookie-api-client.ts` |
| F-06 | 高 | ダッシュボード画面の統計情報が全てハードコード | `app/dashboard/page.tsx` |
| F-07 | 中 | console.logの本番コード残存 | `components/layout/dashboard-layout.tsx` |
| F-08 | 中 | Next.js時代の残骸（デッドコード・命名不整合） | `app/api/`, `app/**/page.tsx` 各所 |
| F-09 | 低 | `cookie-api-client.ts` のドメイン非分割 | `lib/cookie-api-client.ts` |
| F-10 | 低 | Query Key/staleTime方針の不統一 | `hooks/use-cookie-auth-queries.ts`, `hooks/use-cookie-todo-queries.ts` |
| F-11 | 低 | 楽観的更新（Optimistic Updates）が一切未使用 | `hooks/use-cookie-todo-queries.ts` |
| F-12 | 低 | `useCookieTodos` のクライアント側フィルタリング | `components/tasks/task-list.tsx`, `hooks/use-cookie-todo-queries.ts` |
| F-13 | 低 | RBACロジックの文字列ハードコード | `components/auth/auth-guard.tsx` |
| F-14 | 低 | Docker開発用ワークアラウンドの本番バンドル同梱 | `lib/config.ts` |

### 4.1 重大（Critical）

#### F-01: トースト通知（sonner）が実質機能していない

- **事象**：`useUIStore().addNotification()` が `login-form.tsx`、`register-form.tsx`、`task-create-dialog.tsx`、`task-delete-dialog.tsx`、`task-edit-dialog.tsx`、`task-list.tsx` の各所から呼び出され、Zustandストアの `notifications` 配列には要素が積まれる。しかし `frontend/src/components/ui/sonner.tsx` の `Toaster` コンポーネントは `useUIStore` から `theme` のみを参照しており、`notifications` 配列を購読していない。またリポジトリ全体を `toast(` で検索しても、sonnerの `toast()` 関数を呼び出している箇所は0件だった。
- **影響**：ログイン成功/失敗、ログアウト、タスクの作成・更新・削除の成功/失敗など、ユーザーへのフィードバックが本来表示されるべき箇所で一切表示されない。ユーザーから見ると「操作が成功したのか失敗したのか分からない」状態になっており、業務システムの基盤とする上で解消が必須の事項。
- **該当ファイル**：`frontend/src/components/ui/sonner.tsx`、`frontend/src/stores/ui-store.ts`、および `addNotification` を呼び出している各コンポーネント

#### F-02: フロントエンドの自動テストが皆無

- **事象**：リポジトリ全体を `describe(`、`it(`、`vitest`、`@testing-library` 等のキーワードで検索したが該当0件。Vitest、Testing Library、MSW、Playwrightのいずれも導入されていない。`frontend/package.json` にもテスト関連のスクリプト・依存関係が存在しない。
- **影響**：認証・CSRF・SSO/SAMLといったセキュリティ上重要なフローを含め、フロントエンド側の振る舞いを保証する仕組みが一切存在しない。`docs/agent/testing.md` に示されたプロジェクト全体のテスト方針（変更を証明できる最小スコープでのテスト、認証・権限・トークン・SSO/SAML関連変更には統合テストを厚めに当てる方針等）がフロントエンドには適用できていない状態にある。
- **該当ファイル**：`frontend/package.json`（テスト関連依存なし）、リポジトリ全体

#### F-03: CIパイプラインにフロントエンドジョブが存在しない

- **事象**：`.github/workflows/ci.yml`（全79行）を確認したところ、`uv sync --locked --group dev --group test` と `pytest` を `components/libkoiki` と `components/koiki_ref_app` に対して実行するジョブのみが定義されており、`npm ci`、フロントエンドのlint・型チェック・ビルド・テストに相当するステップが一切存在しない。
- **影響**：フロントエンドの型エラー・Lintエラー・ビルド失敗・（将来追加される）テスト失敗がCI上で検知されない。`frontend/README.md` に記載されている検証コマンド（`check-types`、`lint`、`build`）は開発者のローカル実行に依存しており、レビュー・マージ時の機械的な担保がない。
- **該当ファイル**：`.github/workflows/ci.yml`

### 4.2 高（High）

#### F-04: ESLintの実効ルールが未設定

- **事象**：`frontend/eslint.config.mjs`（全7行）の内容は `node_modules/**`、`dist/**`、`build/**` を除外する `ignores` 配列のみであり、TypeScript-ESLint、`eslint-plugin-react-hooks`、jsx-a11y等のルールセットが一切設定・適用されていない。
- **影響**：`npm run lint` を実行してもファイル除外設定が適用されるだけで実質的な静的検査が行われない。開発者が「Lintが機能している」と誤認するリスクがある。
- **該当ファイル**：`frontend/eslint.config.mjs`

#### F-05: TanStack Queryのリトライ抑制ロジックがaxios/fetch不一致で機能していない

- **事象**：`frontend/src/lib/react-query.tsx`（全72行）の `QueryClient` のデフォルトリトライ設定は、エラーが `isAxiosError(error)` であるかを判定し、4xx系エラー（429を除く）の場合はリトライしないという意図の実装になっている。しかし実際のAPI通信は `frontend/src/lib/cookie-api-client.ts` 内で `fetch`（`credentials: "include"`）により行われており、`axios` は `package.json` の依存関係としては存在するが実通信には一切使用されていない。
- **影響**：`isAxiosError(error)` は実際のエラーオブジェクト（`fetch`由来）に対して常に `false` を返すため、意図された「4xxエラー時はリトライしない」というポリシーが機能しない。認証エラー（401）やバリデーションエラー（400）等に対しても不要なリトライが発生し得る状態になっている。
- **該当ファイル**：`frontend/src/lib/react-query.tsx`、`frontend/src/lib/cookie-api-client.ts`

#### F-06: ダッシュボード画面の統計情報が全てハードコード

- **事象**：`frontend/src/app/dashboard/page.tsx`（全151行）内の統計情報（Total Tasks: 12、Completed: 8、In Progress: 4、Team Members: 6）および「Recent Tasks」一覧は、実データ取得用のクエリフックとは接続されておらず、静的な配列としてソースコード内にハードコードされている。
- **影響**：実運用環境でも常に固定値が表示され続けるプロトタイプ/モックアップ状態のままであり、業務システムの土台として利用するには実データ連携（対応するAPIエンドポイントの有無を含めた検討）が必要。
- **該当ファイル**：`frontend/src/app/dashboard/page.tsx`

### 4.3 中（Medium）

#### F-07: console.logの本番コード残存

- **事象**：`frontend/src/components/layout/dashboard-layout.tsx`（全322行）の `handleLogout()` 内に、絵文字付きの `console.log('🚪 Starting logout process...', ...)` 等の `console.log`/`console.error` 呼び出しが、`import.meta.env.DEV` 等の開発環境限定ガードなしに配置されている。他の箇所（例：`use-cookie-auth-queries.ts`、`auth-guard.tsx`）では `devLog` という開発限定ラッパー関数が使われているのと対照的な実装になっている。
- **影響**：本番ビルドでもブラウザのコンソールにログイン/ログアウトのフロー情報が出力され続ける。機密情報の直接漏洩には当たらないが、実装の一貫性のなさとプロダクションコードの品質基準からの逸脱である。
- **該当ファイル**：`frontend/src/components/layout/dashboard-layout.tsx`

#### F-08: Next.js時代の残骸（デッドコード・命名不整合）

- **事象**：
  - `frontend/src/app/api/` が空ディレクトリとして残存している（Next.js Route Handlerの名残）
  - 複数ファイルに意味を持たない `'use client'` ディレクティブが残存している（Viteでは効果を持たない）
  - `frontend/src/app/**/page.tsx` という命名慣習がNext.js App Routerの規約を模しているが、実際のルーティングは `App.tsx` の `BrowserRouter` が担っている（3.2節参照）
- **影響**：新規参画者がNext.js App Routerベースの実装だと誤認する可能性が高く、実際のアーキテクチャ理解を妨げる。`docs/dev/v0.7-frontend-spa-migration/task-4-1.md` にも「stale Next.js-era docs」として複数の旧ドキュメントの整理が申し送り事項として記録されており、コード側にも同種の整理が必要な状態が残っている。
- **該当ファイル**：`frontend/src/app/api/`（空ディレクトリ）、`frontend/src/app/**/page.tsx` 各所

### 4.4 低（設計負債・アンチパターン）

#### F-09: `cookie-api-client.ts` のドメイン非分割

- **事象**：`frontend/src/lib/cookie-api-client.ts`（全381行）は、`CookieApiClient` クラス（CSRF管理・`fetchWithCredentials`ラッパー）に加え、`auth`（login/logout/register/getMe/refreshToken）、`sso`（authorization/login）、`saml`（authorization/login）というプロパティ、さらに `cookieTodoApi`、`cookieUserApi` という独立したトップレベルオブジェクトまで、全ドメインのAPI呼び出しが1ファイルに集約されている。
- **影響**：ドメインが増えるたびにファイルが肥大化し続ける構造であり、責務分割・見通しの点で保守性に課題がある。
- **該当ファイル**：`frontend/src/lib/cookie-api-client.ts`

#### F-10: Query Key/staleTime方針の不統一

- **事象**：`cookieAuthKeys`、`cookieTodoKeys` というQuery Key Factoryパターンが部分的に導入されているが、命名規則・階層設計・ドメインごとのstaleTime使い分け方針がドキュメント化・標準化されていない。
- **影響**：今後ドメインが増えた際に一貫性のないキー設計・キャッシュ方針が量産されるリスクがある。
- **該当ファイル**：`frontend/src/hooks/use-cookie-auth-queries.ts`、`frontend/src/hooks/use-cookie-todo-queries.ts`

#### F-11: 楽観的更新（Optimistic Updates）が一切未使用

- **事象**：`frontend/src/hooks/use-cookie-todo-queries.ts` のミューテーション（作成・更新・削除・トグル）は、いずれも `invalidateQueries`/`removeQueries`/`setQueryData` による再取得・手動反映に依存しており、TanStack Queryの `onMutate` を用いた楽観的更新は一切使用されていない。
- **影響**：ネットワーク遅延時のUXが素朴（操作の都度ローディングを待つ形）であり、業務システムとしての操作性向上余地が残っている。
- **該当ファイル**：`frontend/src/hooks/use-cookie-todo-queries.ts`

#### F-12: `useCookieTodos` のクライアント側フィルタリング

- **事象**：`TodoListParams`/`TodoFilter` という型が定義されているにもかかわらず、`frontend/src/components/tasks/task-list.tsx`（全339行）の検索・完了状態フィルタリングはクライアント側のJavaScriptで行われており、サーバーサイドのクエリパラメータとしては活用されていない。
- **影響**：データ件数が増えた場合にクライアント側フィルタでは非効率になる。型が示す設計意図（サーバーサイドフィルタ対応）と実装が乖離している状態。
- **該当ファイル**：`frontend/src/components/tasks/task-list.tsx`、`frontend/src/hooks/use-cookie-todo-queries.ts`

#### F-13: RBACロジックの文字列ハードコード

- **事象**：`frontend/src/components/auth/auth-guard.tsx`（全165行）内で、`user.roles.map(r => r.name)` から得た文字列配列に対し、`'admin'` 等のロール名を直接文字列比較するロジックがコンポーネント内に埋め込まれている。認可ルールを集約する専用モジュール・定数定義は存在しない。
- **影響**：認可ルールが今後複雑化した際に、コンポーネントごとにロジックが重複・分散するリスクがある。
- **該当ファイル**：`frontend/src/components/auth/auth-guard.tsx`

#### F-14: Docker開発用ワークアラウンドの本番バンドル同梱

- **事象**：`frontend/src/lib/config.ts` 内の `alignLocalhostWithBrowserHost()` はDocker開発環境向けの利便性処理だが、本番ビルド時にも無条件に含まれる実装になっている。
- **影響**：優先度は低いが、本番環境で意図しない挙動を招くリスクがゼロではない。
- **該当ファイル**：`frontend/src/lib/config.ts`

## 5. 維持すべき良好な設計判断

以下は点検の結果、妥当と判断した設計であり、今後の修正作業においても崩さないよう留意する必要がある。

- **バックエンド一元管理の認証・CSRF・SSO/SAML境界設計**（`docs/dev/frontend-spa-migration-plan.ja.md` に基づく）：フロントエンドが実トークンを一切保持せず、一時的なフロー相関データのみを扱う設計思想は堅牢であり、今後の修正でも維持すべき
- **TanStack Queryの基本骨格**（`staleTime`/`gcTime`/リトライの構造自体）：リトライ判定ロジック自体にはバグがある（F-05）が、キャッシュ設計の骨格自体は妥当
- **Zustandの `persist` + `partialize` によるスコープ限定**：永続化対象をUI状態（`sidebarOpen`、`theme`）のみに絞る規律は良い設計判断であり、トークン等の機密情報を誤って永続化するリスクを未然に防いでいる
- **shadcn/ui + Tailwind CSSの選定**：コンポーネントのカスタマイズ性とデザインシステムの一貫性を両立する構成
- **`@/*` パスエイリアスの一貫使用**
- **型定義を集約した `types/` ディレクトリの存在**

## 6. 公式ベストプラクティスとの主な差分（参考情報）

- Query Key Factoryパターンが部分導入に留まり、TanStack Query公式が推奨する規約化されたキー設計になっていない（F-10）
- 楽観的更新（TanStack Query公式が推奨する高度パターンの一つ）が一切活用されていない（F-11）
- `axios` という「実際には使われていない依存関係」が存在し、`fetch` ベースの実装と設計上の意図（リトライロジック）が乖離している（F-05）。依存を除去するか、実際に統一するかの整理が必要
- テスト戦略（Vitest + Testing Library + MSW + Playwrightの組み合わせ等）が一切導入されておらず、React公式・TanStack Query公式のいずれのテストガイドとも整合しない状態（F-02）

## 7. 本ドキュメントのスコープ外事項（次タスクへの申し送り）

- 本ドキュメントは点検・指摘事項の整理までを目的としており、**修正の実装は別タスクとして扱う**
- 修正プランの立案・優先順位付け・実装は次タスクで対応する
- 各指摘事項（F-01〜F-14）は、修正プラン立案時にID単位で参照できるようにしている

## 8. 参考にした資料・調査対象ファイル一覧

### 設計・移行関連ドキュメント

- `docs/dev/frontend-spa-migration-plan.ja.md`
- `docs/dev/v0.7-frontend-spa-migration/README.ja.md`
- `docs/dev/v0.7-frontend-spa-migration/task-4-1.md`
- `docs/dev/frontend-review-antigravity.md`
- `docs/agent/testing.md`
- `frontend/README.md`
- （参考・旧世代・現状不整合）`docs/FRONTEND_ENTERPRISE_AUDIT_ja.md`、`docs/frontend-application-development-guide.md`

### 設定ファイル

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/eslint.config.mjs`
- `.github/workflows/ci.yml`

### ソースコード

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/lib/config.ts`
- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/lib/react-query.tsx`
- `frontend/src/stores/ui-store.ts`
- `frontend/src/hooks/use-cookie-auth-queries.ts`
- `frontend/src/hooks/use-cookie-todo-queries.ts`
- `frontend/src/hooks/use-sso-login.ts`
- `frontend/src/hooks/use-saml-login.ts`
- `frontend/src/components/auth/auth-guard.tsx`
- `frontend/src/components/auth/login-form.tsx`
- `frontend/src/components/layout/dashboard-layout.tsx`
- `frontend/src/components/tasks/task-list.tsx`
- `frontend/src/components/ui/sonner.tsx`
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/app/sso/callback/page.tsx`