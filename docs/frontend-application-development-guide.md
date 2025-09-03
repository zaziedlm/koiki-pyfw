# フロントエンド アプリケーション開発ガイド（Next.js 15 + FastAPI）

最終更新: 2025-09-03

本ガイドは、本リポジトリの `frontend/` に実装されたダッシュボード、ログイン画面、Task（Todo）管理機能を基に、同様の機能を今後拡張/追加する開発者向けに技術情報・アーキテクチャ・バックエンド FastAPI との連携方式を体系化したものです。

- 対象フレームワーク: Next.js 15（App Router, React 19）
- 認証方式: httpOnly Cookie ベースの JWT + CSRF ダブルサブミット
- データ同期: TanStack Query（React Query）
- UI/状態: shadcn/ui + Tailwind、Zustand（UI 状態のみ）

関連ドキュメント:
- `docs/dev/frontend-next15-guide.md`（実装精査レポートと改善指針）
- `docs/authentication-api-guide.md`（FastAPI 側の認証API完全ガイド）


## 1. 全体アーキテクチャ

### 1.1 構成概要（BFF/Route Handlers + Cookie 認証）

フロントエンドは Next.js の Route Handlers（`src/app/api/**`）を薄い BFF として使用します。ブラウザとバックエンド FastAPI の間に Next 層を挟むことで、以下を実現しています。

- 認証トークンは httpOnly Cookie（`koiki_access_token` など）で保持し、JS から不可視
- CSRF 対策（ヘッダーと Cookie のダブルサブミット）
- CORS 煩雑さの軽減（同一オリジン `/api/**` で集約）
- エラーメッセージの整形や監査ログ出力の集約

主要ディレクトリ/ファイル（抜粋）:
- フロントエンド UI: `frontend/src/app/**`, `frontend/src/components/**`
- 認証フロー（フロント）: `frontend/src/hooks/use-cookie-auth-queries.ts`, `frontend/src/components/auth/**`
- タスク機能（フロント）: `frontend/src/hooks/use-cookie-todo-queries.ts`, `frontend/src/components/tasks/**`
- Route Handlers（BFF）: `frontend/src/app/api/**`
- CSRF/Cookie ユーティリティ: `frontend/src/lib/csrf-utils.ts`, `frontend/src/lib/cookie-utils.ts`, `frontend/src/lib/cookie-api-client.ts`
- ルーティング保護: `frontend/src/middleware.ts`


### 1.2 ページ/レイアウト

- ダッシュボード: `frontend/src/app/dashboard/page.tsx`
- タスク一覧: `frontend/src/app/dashboard/tasks/page.tsx`
- ログイン: `frontend/src/app/auth/login/page.tsx`
- 共通レイアウト（サイドバー/ヘッダー）: `frontend/src/components/layout/dashboard-layout.tsx`

ページは基本的に RSC を維持しつつ、ユーザー操作を伴う箇所をクライアントコンポーネント化（`'use client'`）します。


## 2. 認証アーキテクチャ

### 2.1 Cookie ベース JWT + CSRF（ダブルサブミット）

- アクセストークン: httpOnly Cookie `koiki_access_token`
- リフレッシュトークン: httpOnly Cookie `koiki_refresh_token`
- CSRF トークン: 非 httpOnly Cookie `koiki_csrf_token` とヘッダー `x-csrf-token`

関連コード:
- CSRF 生成: `frontend/src/app/api/auth/csrf/route.ts`
- CSRF 検証: `frontend/src/lib/csrf-utils.ts`（GET はスキップ、非 GET は Cookie とヘッダー一致を確認）
- Cookie 設定/消去: `frontend/src/lib/cookie-utils.ts`
- 認証 API クライアント: `frontend/src/lib/cookie-api-client.ts`

フロー（ログイン）:
1) 事前に `/api/auth/csrf` へ GET して `koiki_csrf_token` を受領
2) `x-csrf-token` ヘッダーを付与して `/api/auth/login` へ POST
3) Route Handler が FastAPI `/auth/login` へプロキシし、返却された JWT を httpOnly Cookie 化
4) 成功後、`/api/auth/me` でユーザー情報を取得・キャッシュ

実装参照:
- Hook: `useCookieLogin`, `useCookieMe`, `useCookieAuth`（`frontend/src/hooks/use-cookie-auth-queries.ts`）
- UI: `LoginForm`（`frontend/src/components/auth/login-form.tsx`）
- Guard: `AuthGuard`, `ProtectedRoute`, `PublicRoute`（`frontend/src/components/auth/auth-guard.tsx`）


### 2.2 Route Handlers（BFF）

Route Handlers はバックエンドの FastAPI をプロキシします。

- 認証系: `frontend/src/app/api/auth/*`（login/logout/me/refresh/csrf）
- タスク系: `frontend/src/app/api/todos/**`

ポイント:
- 非 GET の場合は `validateCSRFToken` を通す
- バックエンド呼出時は Cookie のアクセストークンを `Authorization: Bearer <token>` へ転写
- 失敗時のメッセージ統一・ログ出力

環境設定:
- `NEXT_PUBLIC_API_URL`（例: `http://localhost:8000`）
- `NEXT_PUBLIC_API_PREFIX`（例: `/api/v1`）
- `next.config.ts` の rewrites で `/api/backend/:path*` → バックエンドの API へも対応可能


### 2.3 middleware によるルート保護

`frontend/src/middleware.ts` にて、以下プレフィックス配下を保護します。

- `/dashboard`, `/profile`, `/admin`, `/settings`

現在は Cookie の存在/JWT 形式を確認してログインページへリダイレクトします。要件に応じて、デコード・期限チェックや `/api/auth/me` の軽量検証へ拡張可能です。


## 3. タスク（Todo）機能の実装パターン

### 3.1 データ取得/更新（React Query）

- Hook 定義: `frontend/src/hooks/use-cookie-todo-queries.ts`
  - list: `useCookieTodos(params)`
  - detail: `useCookieTodo(id)`
  - create: `useCookieCreateTodo()`
  - update: `useCookieUpdateTodo()` / `useCookieToggleTodo()`
  - delete: `useCookieDeleteTodo()`

キャッシュ戦略:
- list: `staleTime` 30s、`queryKey` へフィルタを含める
- update/delete: `setQueryData` で detail を即時更新 + list を invalidate

BFF 経由のエンドポイント:
- GET/POST: `frontend/src/app/api/todos/route.ts`
- GET/PUT/DELETE（id 指定）: `frontend/src/app/api/todos/[id]/route.ts`


### 3.2 UI コンポーネント

- 一覧: `frontend/src/components/tasks/task-list.tsx`
- 作成/編集/削除ダイアログ: `frontend/src/components/tasks/*-dialog.tsx`

主な UI/UX 仕様:
- 検索・完了/未完了フィルタ（クライアント側フィルタ + React Query での将来拡張を想定）
- 完了トグルは `useCookieUpdateTodo` を利用
- 操作結果は `useUIStore` の通知でフィードバック


## 4. ダッシュボード/ナビゲーション

- レイアウト: `DashboardLayout`（`frontend/src/components/layout/dashboard-layout.tsx`）
- ルート: `/dashboard`, `/dashboard/tasks`, ほか
- ユーザーメニュー: ログアウトは `useCookieLogout` 経由で Cookie 破棄 → `/auth/login` へ遷移
- ナビゲーション権限制御: `useCookieAuth()` の `user.roles` / `is_superuser` でフィルタリング


## 5. ログイン画面/フォーム

- ページ: `frontend/src/app/auth/login/page.tsx`
- フォーム: `LoginForm`（`react-hook-form` + `zod`）
- 提交: `useCookieLogin().mutateAsync({ email, password })`
- 成功後: `useCookieLogin` が `cookieAuthKeys` を invalidation → Cookie 伝播を軽量ポーリングで確認 → `/dashboard` へ遷移


## 6. CSRF 対策の詳細

方式: ダブルサブミット（Cookie + ヘッダー）

- 取得: `GET /api/auth/csrf` で `koiki_csrf_token` を Cookie とレスポンス body に返す
- 付与: `cookie-api-client.ts` が `x-csrf-token` ヘッダーを自動付与（不足時は再取得）
- 検証: `validateCSRFToken` が非 GET のみ Cookie とヘッダーの一致を確認し、失敗時は 403 と `CSRF_TOKEN_INVALID` を返却

実装参照:
- `frontend/src/app/api/auth/csrf/route.ts`
- `frontend/src/lib/cookie-api-client.ts`
- `frontend/src/lib/csrf-utils.ts`


## 7. バックエンド FastAPI 連携

Route Handlers → FastAPI:

- `getBackendApiUrl()`（`frontend/src/lib/cookie-utils.ts`）で `NEXT_PUBLIC_API_URL` + `NEXT_PUBLIC_API_PREFIX` を合成
- 認証: Cookie のアクセストークンを `Authorization: Bearer` で転送
- タスク: `/todos`（一覧/詳細/更新/削除）
- 認証: `/auth/login`, `/auth/me`, `/auth/refresh`, `/auth/logout`

バックエンドの仕様詳細は `docs/authentication-api-guide.md` を参照してください（OAuth2 互換の `/auth/login`、リフレッシュ `/auth/refresh`、試行制限、監査など）。


## 8. 新機能（リソース）追加の手順テンプレート

例: 新規ドメイン「Projects」を追加する場合

1) バックエンド（FastAPI）
   - `GET /projects`, `POST /projects`, `GET /projects/{id}`, `PUT /projects/{id}`, `DELETE /projects/{id}` を実装
   - 認可（RBAC/権限）とスキーマを定義

2) Route Handlers（BFF, Next）
   - `frontend/src/app/api/projects/route.ts`（GET/POST）
   - `frontend/src/app/api/projects/[id]/route.ts`（GET/PUT/DELETE）
   - 非 GET は `validateCSRFToken` を必須化

3) API クライアント（Cookie 版）
   - `frontend/src/lib/cookie-api-client.ts` に `cookieProjectApi` を追加
   - CSRF が必要なメソッドは `initializeCSRFToken()` 確認

4) React Query Hooks
   - `frontend/src/hooks/use-cookie-project-queries.ts` を作成（list/detail/mutations）
   - `queryKey` を `['cookie-projects', ...]` で定義

5) UI/ページ
   - 一覧/詳細/作成/編集/削除のコンポーネント群（`frontend/src/components/projects/**`）
   - ルート: `/dashboard/projects` を追加し `ProtectedRoute` で保護

6) ナビゲーション/権限
   - `DashboardLayout` の `navigation` にメニュー項目を追加し、必要なら `roles` を指定

7) 動作確認/品質ゲート
   - フロント: `npm run dev` で手動確認、React Query のキャッシュ/エラー動作を確認
   - Lint/TS: `next.config.ts` は本番で無効化しない（既定は有効）
   - e2e は Playwright 導入を推奨（任意）


## 9. エラー処理と通知

- API 失敗時は `throw new Error(message)` で UI へ伝播
- フォーム/ミューテーションの失敗は `useUIStore().addNotification({ type: 'error', ... })` でトースト表示
- 認証 401 は `useCookieAuth` の `isAuthenticated` で UX 制御 + `middleware` で一次防御
- CSRF 403（`CSRF_TOKEN_INVALID`）は `cookie-api-client.ts` が再取得→リトライを実施


## 10. セキュリティ実務ポイント

- トークンは常に httpOnly Cookie。localStorage は使用しない
- Cookie 属性: `Secure`（本番）、`SameSite=Lax`、`Path=/`
- `fetch` は `credentials: 'include'`
- 非 GET は CSRF 検証を通す
- 管理系 UI は `roles`/`is_superuser` でガード
- ログ出力は開発時のみに抑制（機密値は出力しない）


## 11. パフォーマンス/品質

- React Query の `staleTime`/`enabled` を適切化（例: 一覧 30〜60s）
- キャッシュ更新は list invalidate + detail `setQueryData` の併用
- `'use client'` を必要箇所へ限定
- `next.config.ts` で Lint/TS を本番でも有効（本リポジトリは既に有効化済み）


## 12. 環境変数/設定

- `NEXT_PUBLIC_API_URL`（例: `http://localhost:8000`）
- `NEXT_PUBLIC_API_PREFIX`（例: `/api/v1`）
- `NEXT_PUBLIC_APP_NAME` / `NEXT_PUBLIC_APP_VERSION`
- Cookie 認証の ON/OFF は `frontend/src/lib/config.ts` の `auth.cookieAuth.enabled` を参照（既定: 有効）

`next.config.ts` の rewrites:

- `/api/backend/:path*` → `${API_URL}${API_PREFIX}/:path*`
- 直接バックエンドを叩く代わりに、BFF（`/api/**`）または rewrites を使ってオリジン統一を推奨


## 13. トラブルシュート

- 401 Unauthorized（`/api/auth/me`）
  - Cookie が付与されていない/ドメイン不一致/HTTP アクセス
  - `middleware` によるリダイレクトを確認
  - バックエンド CORS/オリジン設定を再確認

- 403 CSRF_TOKEN_INVALID
  - `x-csrf-token` が欠落/不一致。`/api/auth/csrf` が取得できているか確認
  - 複数タブでトークン競合が起きた場合は自動再取得/再試行に任せる

- Cookie がブラウザに保存されない
  - 本番は HTTPS + `Secure` 必須
  - サブドメイン/パス/`SameSite` の整合を確認


## 14. 参考: 主要コードの意図

- `use-cookie-auth-queries.ts`
  - `useCookieLogin`: ログイン成功→ユーザーキャッシュ設定→クエリ無効化→Cookie 伝播待ち→リダイレクト
  - `useCookieMe`: 401 を「未認証」として扱い、UI で分岐しやすく

- `cookie-api-client.ts`
  - `fetchWithCredentials`: `credentials: 'include'` と CSRF ヘッダー付与を一元化
  - 403（CSRF）時はトークン更新→1回リトライ

- Route Handlers（`/api/auth/*`, `/api/todos/*`）
  - 非 GET の CSRF 検証、Cookie→Bearer 転写、失敗時の NextResponse 整形

- `middleware.ts`
  - 保護ルートの簡易ガード。必要に応じて厳格化可


---

要約: 本フロントエンドは「Cookie 認証 + CSRF + Route Handlers（BFF）」を基本に、React Query でサーバ同期を一元化し、Zustand は UI 状態に限定しています。新規ドメイン機能は「BFF → Cookie API クライアント → React Query Hooks → UI」の層構成を踏襲すれば、安全で一貫した実装が可能です。
