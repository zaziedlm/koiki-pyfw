# フロントエンド エンタープライズ対応度監査（Next.js 15）

- 対象: `frontend/`（Next.js 15, React 19, App Router）
- バックエンド: FastAPI（Next ルートハンドラ経由の BFF 構成）
- 日付: 2025-09-04

## エグゼクティブサマリー

本プロトタイプは、エンタープライズ向け要件に対して堅実な基盤を備えています。具体的には、httpOnly クッキーを用いた安全な認証、二重送信トークンによる CSRF 対策、Docker におけるハードニング（非 root、独自 CA 信頼設定）、UI と BFF の適切な分離などです。一方で、運用段階に向けては、主要なセキュリティヘッダー（CSP / HSTS / COOP/COEP/CORP / Referrer-Policy / Permissions-Policy）の追加、BFF ルートのレート制限、可観測性（Sentry / OpenTelemetry）の導入、フロントエンド CI の不足など、強化ポイントが残っています。稼働前に修正すべき小さな不具合もいくつか存在します（後述）。

リスク評価: 中（優先対応により解消可能）

## 強み（ハイライト）

- 認証トークンは httpOnly Cookie に格納（WebStorage 不使用）
  - 参照: `frontend/src/lib/cookie-utils.ts:1` および各認証ルートでの使用
- CSRF: 二重送信（Cookie + ヘッダー）。認証フロー後に再発行
  - 参照: `frontend/src/lib/csrf-utils.ts:1`, `frontend/src/app/api/auth/csrf/route.ts:1`
- BFF: Next の Route Handler でバックエンドへプロキシし、トークンをブラウザから秘匿
  - 参照: `frontend/src/app/api/**` のプロキシ実装
- Cookie 属性は適切（httpOnly, SameSite=Lax, 本番時 Secure）
  - 参照: `frontend/src/lib/cookie-utils.ts:18`
- Docker: マルチステージ、非 root、独自 CA、ヘルスチェック
  - 参照: `frontend/Dockerfile:1`
- App Router 採用と責務分離、TanStack Query によるデータ取得

## ギャップとリスク（サマリー）

- 重要ヘッダー不足（CSP, Referrer-Policy, HSTS, COOP/COEP/CORP, Permissions-Policy）。現状は `X-Frame-Options`, `X-Content-Type-Options` のみ
  - 参照: `frontend/next.config.ts:24`
- BFF ルートの濫用対策が未実装（レート制限、Bot 対策、単純スロットリング等）
- 可観測性の不足（Sentry, OpenTelemetry の未導入、構造化ログの不足）
- フロントエンド CI なし（型チェック、lint、ビルド、テストがワークフローに未統合）
  - 参照: `.github/workflows/ci.yml` はバックエンドのみ
- ミドルウェアの runtime エクスポートが Next の仕様に不適合（削除推奨）
  - 参照: `frontend/src/middleware.ts:5`
- 軽微な不具合: `cookie-api-client.ts` での変数重複定義（型チェック/ビルドで問題化）
  - 参照: `frontend/src/lib/cookie-api-client.ts:218-224`（ユーザー一覧の類似箇所 `:277-280` も確認）
- 一部ルートハンドラで本番でもログ出力（機密情報は含まれていないが抑制推奨）
  - 参照: `frontend/src/app/api/auth/login/route.ts:57`

---

## 詳細観点

### 1) 認証・セッション管理

- httpOnly + SameSite=Lax + 本番 Secure のクッキー設定
  - 参照: `frontend/src/lib/cookie-utils.ts:18`
- CSRF: Cookie（`koiki_csrf_token`）とヘッダー（`x-csrf-token`）の一致検証。ログイン/登録/リフレッシュで都度更新
  - 参照: `frontend/src/lib/csrf-utils.ts:1`, `frontend/src/app/api/auth/csrf/route.ts:1`
  - 変更系 API（todos/users）で適用済み
    - 例: `frontend/src/app/api/todos/route.ts:1`（POST）、`frontend/src/app/api/users/[id]/route.ts`（PUT/DELETE）
- 推奨:
  - 本番では Cookie 名に `__Host-` プレフィックスを付与し、`path=/`・`domain` 未指定・`Secure` 強制を徹底
  - BFF 側で不透明セッション ID 方式 or 短寿命 Access Token + 厳格な Refresh Token ローテーション
  - 盗難/再利用検知（Refresh 再利用検知など）をバックエンドで実装し、最小限の UX シグナルをフロントに提供

### 2) セキュリティヘッダー・プラットフォームハードニング

- 現状ヘッダー: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`
  - 参照: `frontend/next.config.ts:24`
- 追加推奨（`NEXT_PUBLIC_ENABLE_SECURITY_HEADERS` で制御）:
  - CSP: nonce もしくはハッシュベースで厳格化（Next.js に合わせて scripts/styles/fonts/images を許可）。まずは Report-Only をステージングで適用
  - Referrer-Policy: `strict-origin-when-cross-origin`
  - HSTS: TLS 配下で有効化（`includeSubDomains; preload` は要検討）
  - Permissions-Policy: camera/microphone/geolocation 等の利用を明示的に制限
  - Cross-Origin-* 系: COOP `same-origin`, CORP `same-origin`,（必要に応じて）COEP
  - 機微な BFF 応答のキャッシュ制御: `no-store` または `private, no-store`

例（`next.config.ts` 抜粋。実運用環境に合わせて調整）:

```ts
// next.config.ts (excerpt)
async headers() {
  const enabled = process.env.NEXT_PUBLIC_ENABLE_SECURITY_HEADERS === 'true';
  if (!enabled) return [];
  return [
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        // HTTPS 配下のみ有効化
        // { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
        { key: 'Cross-Origin-Resource-Policy', value: 'same-origin' },
        // プロセス分離が必要な場合のみ
        // { key: 'Cross-Origin-Embedder-Policy', value: 'require-corp' },
      ],
    },
  ];
}
```

CSP は本番で `script-src 'self' 'nonce-<generated>'` を推奨。レイアウトで nonce を付与し、`unsafe-inline` は避けること。

### 3) BFF ルートハンドラ（API）

- サーバー側 Cookie による認証伝播でブラウザへトークン露出なし
  - 例: `frontend/src/app/api/auth/*`, `.../todos/*`, `.../users/*`
- 一部で `cache: 'no-store'` を明示（良い）が、未統一
  - 例: `frontend/src/app/api/users/me/route.ts:18` は `no-store` 指定。その他も統一化推奨
- 推奨:
  - 認証依存の BFF 応答は `no-store` を徹底。キャッシュ不可のルートは `export const dynamic = 'force-dynamic'` も検討
  - バックエンドのエラーメッセージは共通整形し、クライアントに露出される情報を最小化
  - 重要な更新系は冪等性キーの導入も検討

### 4) ミドルウェア

- `export const runtime = 'nodejs'` はミドルウェアでは非対応（Next 15 のミドルウェアは Edge ランタイム固定）。削除推奨
  - 参照: `frontend/src/middleware.ts:5`
- JWT の「形式」チェックは軽量で妥当。本検証は BFF/バックエンド側に委任し、ミドルウェアは軽量を維持

### 5) 可観測性・監査性

- 現状、集中管理されたエラーレポート／トレースが未導入
- 推奨:
  - Sentry（ブラウザ + Route Handlers）を導入し、PII マスキングを適用
  - OpenTelemetry で BFF→バックエンドの分散トレースを可視化（OTLP Collector 連携）
  - サーバーサイドは構造化ロガーを使用し、本番はコンソールログを抑制/転送

### 6) 濫用防止

- BFF と認証関連ルートにレート制限なし。ログイン/登録/リフレッシュ/CSRF 発行に IP ベースの簡易スロットリングを推奨
  - 開発ではメモリ/LRU、本番では Redis/Upstash など
- 公開フォームには Bot 対策（Turnstile/reCAPTCHA）も検討

### 7) CI/CD・テスト

- フロントエンド向け CI ジョブが未定義（バックエンドのみ）
- 推奨:
  - Node LTS で `npm ci` → `npm run lint` → `tsc --noEmit` → `npm run build`
  - 重要ユーティリティ/フックの単体テスト（Vitest）
  - e2e スモーク（Playwright）: ログイン、ダッシュボードアクセス、Todo CRUD
  - CI のゲートを型/ lint / テスト/ビルド成功に連動

### 8) アクセシビリティ・i18n

- ESLint は Next 既定（a11y ルールを含む）を使用
  - 参照: `frontend/eslint.config.mjs:1`
- 推奨:
  - 自動 a11y チェック（axe + Playwright）とキーボード/スクリーンリーダ確認を CI に組込み
  - 多言語要件がある場合は i18n（`next-intl` / `next-i18next`）を導入し、ロケールルーティングを整備

### 9) パフォーマンス・UX

- TanStack Query のデフォルト設定は妥当。保護ページで SSR を強要していない点も適切
- 推奨:
  - 更新頻度に応じて `staleTime` / `gcTime` を個別最適化
  - 大型コンポーネントの遅延読み込みやルートレベルのストリーミング適用
  - 静的アセットの `Cache-Control` を Next 設定 or CDN 側で適切に設定

### 10) Docker・サプライチェーン

- マルチステージ、非 root、独自 CA 信頼、ヘルスチェックは良好
  - 参照: `frontend/Dockerfile`
- 推奨:
  - ベースイメージをダイジェスト固定し再現性を確保
  - 本番イメージの不要ファイル除去（既に `--omit=dev` 使用）
  - 依存更新（Dependabot / Renovate）と脆弱性監査の定期実行

---

## 即時修正（優先度高）

1) ミドルウェアの runtime エクスポート削除
- 対象: `frontend/src/middleware.ts:5`
- 内容: `export const runtime = 'nodejs';` を削除（Next 15 のミドルウェアは Edge 固定）

2) 変数重複定義の修正（型/ビルド阻害）
- 対象: `frontend/src/lib/cookie-api-client.ts:218-224`
- 内容: `cookieTodoApi.getAll` 内の `const queryString` が重複。片方を削除し単一定義へ。ユーザー一覧の `:277-280` も要確認

3) 本番ログ抑制
- 対象: `frontend/src/app/api/auth/login/route.ts:57`
- 内容: `if (process.env.NODE_ENV === 'development') { ... }` で制御、またはサーバーロガーへ統一

4) セキュリティヘッダーの包括導入
- 対象: `frontend/next.config.ts`
- 内容: CSP / Referrer-Policy / HSTS / COOP/CORP / Permissions-Policy を環境変数で制御して適用

5) 認証系・CSRF ルートへのレート制限
- 対象: `frontend/src/app/api/auth/*`, `frontend/src/app/api/auth/csrf/route.ts`
- 内容: IP ベースのスロットリング（開発: メモリ、商用: Redis/Upstash）

---

## 推奨次ステップ（優先順）

1) セキュリティヘッダーと CSP（ステージングは Report-Only、本番は厳格）
2) ミドルウェア修正、重複変数の修正
3) フロントエンド CI 追加（lint / 型 / ビルド）、Playwright と Vitest の最小テスト導入
4) Sentry / OpenTelemetry の導入
5) 公開/認証 BFF へのレート制限追加、ログイン/登録に Bot 対策
6) Cookie の `__Host-` 化、バックエンドでの Refresh ローテーション確認
7) BFF 応答の `no-store` 統一（ユーザー依存データのキャッシュ禁止）
8) 依存更新ポリシー（Dependabot/Renovate）と `npm audit` 運用
9) i18n と a11y テスト（要件次第）
10) 運用 Runbook 整備（トークンインシデント対応、CSRF ローテ、ヘッダー回帰テスト）

---

## 参考ファイルパス（抜粋）

- ミドルウェア: `frontend/src/middleware.ts:1`
- セキュリティヘッダー: `frontend/next.config.ts:1`
- Cookie ユーティリティ: `frontend/src/lib/cookie-utils.ts:1`
- CSRF ユーティリティ: `frontend/src/lib/csrf-utils.ts:1`
- CSRF エンドポイント: `frontend/src/app/api/auth/csrf/route.ts:1`
- 認証ルート: `frontend/src/app/api/auth/login/route.ts:1`, `.../refresh/route.ts:1`, `.../logout/route.ts:1`, `.../register/route.ts:1`, `.../me/route.ts:1`
- Todos BFF: `frontend/src/app/api/todos/route.ts:1`, `.../todos/[id]/route.ts:1`
- Users BFF: `frontend/src/app/api/users/route.ts:1`, `.../users/[id]/route.ts:1`, `.../users/me/route.ts:1`
- クライアント API クライアント: `frontend/src/lib/cookie-api-client.ts:1`
- 設定/環境サンプル: `frontend/.env.local.example:1`, `frontend/.env.docker:1`
- Docker: `frontend/Dockerfile:1`
- CI（バックエンドのみ）: `.github/workflows/ci.yml:1`

---

## 補足

本プロトタイプは、モダンな Next.js のパターンを踏まえた堅牢な認証基盤を有しています。特に、CSP を含むセキュリティヘッダー、レート制限、可観測性、フロントエンド CI の整備を優先実装することで、エンタープライズレベルへ到達可能です。ご要望があれば、ミドルウェア修正・重複変数修正・セキュリティヘッダー導入の小規模 PR を作成します。

