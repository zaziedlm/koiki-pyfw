# KOIKI Frontend 実装精査レポートと Next.js 15 開発ガイド（改訂）

最終更新: 2025-09-03

本書はフロントエンド実装（Next.js 15 / React 19）の現状に合わせて最新化した開発ガイドです。詳細なアーキテクチャと実装パターンは、あわせて作成した「フロントエンド アプリケーション開発ガイド」を参照してください。

- 参照: `docs/frontend-application-development-guide.md`

---

## 1. 現状サマリ（実装と整合済み）

### 1.1 技術スタック/設定
- Next.js 15 / React 19 / App Router / Tailwind 構成
- `next.config.ts` は ESLint/TypeScript のチェックをビルド時に有効（ignoreDuringBuilds=false, ignoreBuildErrors=false）
- rewrites: `/api/backend/:path* -> ${NEXT_PUBLIC_API_URL}${NEXT_PUBLIC_API_PREFIX}` を定義（将来の直接プロキシに利用可能）

### 1.2 App Router/レイアウト
- ページ配下は基本 RSC、ユーザー操作・エフェクトが必要な箇所のみクライアント化
- レイアウト/ナビゲーションは `components/layout/dashboard-layout.tsx`

### 1.3 認証と middleware（Cookie + CSRF + BFF）
- 認証は httpOnly Cookie（`koiki_access_token`/`koiki_refresh_token`）へ統一
- 非 GET は CSRF ダブルサブミット（Cookie `koiki_csrf_token` とヘッダー `x-csrf-token`）
- BFF（Route Handlers）で FastAPI をプロキシ（`src/app/api/auth/*`, `src/app/api/todos/*`）
- `middleware.ts` で `/dashboard` 等の保護ルートを Cookie ベースでガード

### 1.4 データ取得/更新
- TanStack Query（React Query）を標準。サーバ同期は Hooks に集約
  - 認証: `use-cookie-auth-queries.ts`（login/me/logout/refresh）
  - タスク: `use-cookie-todo-queries.ts`（list/detail/create/update/delete/toggle）
- `react-query.tsx` で retry 分岐に `isAxiosError` を使用（Devtools は開発時のみ）
- API 呼出は主に BFF `/api/**` を利用（`cookie-api-client.ts` が CSRF ヘッダー付与/再取得を内包）

### 1.5 状態管理
- Zustand は UI 状態（通知/テーマ/サイドバー）に限定（`stores/ui-store.ts`）
- サーバ同期データは React Query に一本化（重複保持なし）

### 1.6 UI/スタイル
- shadcn/ui + Tailwind。テーマ切替は UI ストアで制御

---

## 2. 改善提案（現状に沿った軽微なもの）

優先度P2-P3 の運用/保守性向上メモです。主要な P1 はすでに対応済み（Cookie 認証統一、CSRF、Lint/TS 有効、Devtools 制御）。

1) middleware の厳格化（任意）
- Cookie 存在チェックに加え、期限を軽く検証する or `/api/auth/me` を軽量叩きで確認

2) rewrites の活用ポリシー整理（任意）
- 基本は BFF（`/api/auth/*`, `/api/todos/*`）で統一。将来の直接プロキシは `/api/backend/*` に集約

3) 観測性・テレメトリ（任意）
- 重要操作（認証・タスク変更）のクライアントログを開発時のみに抑制し、監査はサーバ側で

4) e2e/契約テストの整備（任意）
- Playwright や Contract Test（FastAPI スキーマ準拠）

---

## 3. 実装パターン/テンプレート（最新版）

### 3.1 セキュア fetch（BFF 経由, Cookie 認証）
- `credentials: 'include'` を必須にし、非 GET は `x-csrf-token` を付与（`cookie-api-client.ts` が自動化）

### 3.2 Route Handlers（BFF）設計
- 非 GET は `validateCSRFToken` を通す
- Cookie のアクセストークン → `Authorization: Bearer` へ転写して FastAPI に転送
- エラーは NextResponse で整形し、機密値はログ出力しない

### 3.3 React Query（list/detail/mutation）
- list: `staleTime` 30–60s、フィルタは `queryKey` に含める
- 書換後: detail は `setQueryData` で即時反映 + list invalidate

---

## 4. ディレクトリ/命名指針
- `app`: ルーティング（RSC デフォルト）
- `components`: 再利用 UI（副作用なしを基本）
- `hooks`: React Query Hooks（サーバ同期はここに集約）
- `lib`: config / cookie-api-client / csrf-utils / utils / react-query
- `stores`: UI ローカル状態（Zustand）。サーバ同期は持たない
- `types`: API DTO/型定義

---

## 5. 環境変数/rewrites 指針
- `.env.local` 例（抜粋）
  - `NEXT_PUBLIC_APP_NAME`
  - `NEXT_PUBLIC_APP_VERSION`
  - `NEXT_PUBLIC_API_URL`（例: `http://localhost:8000`）
  - `NEXT_PUBLIC_API_PREFIX`（例: `/api/v1`）
- `next.config.ts`: rewrites で `/api/backend/:path*` を定義済み
- 実装上は BFF `/api/**`（Route Handlers）を優先利用

---

## 6. 品質/セキュリティ標準
- ESLint/TS チェックはビルドで有効
- Cookie 認証 + CSRF（二重送信）必須
- 開発時のみ詳細ログ。機密値は出力しない
- 依存監査（npm audit など）

---

## 7. 開発フロー（新機能追加時の要点）
1) FastAPI にエンドポイントを追加（認可/スキーマ定義）
2) Next の BFF を追加（`/api/<resource>/**`、非 GET は CSRF 検証）
3) `cookie-api-client.ts` に API メソッド（必要に応じて）
4) React Query Hooks を追加（list/detail/mutations）
5) UI/ページを追加し `ProtectedRoute` で保護
6) ナビゲーションに統合、必要なら `roles` で絞り込み

詳細手順は `docs/frontend-application-development-guide.md` の「新機能追加の手順テンプレート」を参照。

---

## 8. チェックリスト（更新）
- [x] Lint/TS を本番ビルドで有効
- [x] 認証を httpOnly Cookie + CSRF に統一
- [x] React Query Devtools は開発時のみ
- [x] サーバ同期は React Query に一本化、Zustand は UI のみ
- [ ] middleware の検証強化（任意）
- [ ] e2e/契約テストの導入（任意）

---

保存場所: `docs/dev/frontend-next15-guide.md`
