# フロントエンド実装 点検レポート（バックエンド連携視点）

本レポートは、`frontend/` 以下の実装（第3章：ログイン機能、ダッシュボード画面、Todoタスク管理画面）について、バックエンド API 連携・セキュリティの観点から点検した結果をまとめたものです。Next.js App Router（Route Handlers/BFF）、Cookie ベースの認証、CSRF 対策、権限制御、UI からの API 呼び出し経路などを中心に評価しています。

## 総評（サマリ）

- 構成の全体像は妥当で、BFF（Next.js Route Handlers）を介した「httpOnly Cookie + CSRF」方式の実装は堅牢性が高いです。
- 認証・権限・CSRF に関する基本的なガードは概ね適切に配置されています（ミドルウェア、AuthGuard、Route Handler 側の検証など）。
- 一部、未使用（もしくは将来拡張向け）のコードが「バックエンドへ直接アクセスする実装」になっており、現状の Cookie ベース方針とは齟齬があります（CORS/Authorization 未付与）。利用の有無を明確化の上、BFF 経由に統一する改善が望ましいです。
- 実運用を意識した堅牢化（CSP 等の追加ヘッダ、トークン有効期限の事前判定、CSRF トークンのライフサイクル運用、リフレッシュ自動連携など）でさらに強固にできます。

---

## 実装アーキテクチャの把握

- 認証方式
  - `httpOnly` なアクセストークン／リフレッシュトークン（`koiki_access_token`／`koiki_refresh_token`）を Cookie に保存。
  - 状態変化を伴う操作は、`/src/app/api/**` の Route Handler（BFF）を経由し、CSRF トークン検証を実施。
  - UI 側は `@tanstack/react-query` を用いて `/api/**`（フロント同一オリジン）に対して fetch。サーバ側 Route Handler でバックエンドへ委譲し、`Authorization: Bearer` を付与。

- CSRF 対策
  - ダブルサブミットクッキー方式。JS から参照可能な `koiki_csrf_token` を Cookie に設定し、ヘッダ `x-csrf-token` と照合。
  - GET は免除、POST/PUT/DELETE など状態変更系で検証。

- ルーティング/ガード
  - Next.js Middleware による保護ページの入口ガード（Cookie の有無/形式）。`frontend/src/middleware.ts:1`。
  - クライアント側の `AuthGuard` によるガード（未認証時のリダイレクト、ロール判定の UI 制御）。`frontend/src/components/auth/auth-guard.tsx:1`。
  - Route Handler 側でも `/api/users/**` でサーバサイドの管理者判定を実施し二重化。`frontend/src/app/api/users/route.ts:1`、`frontend/src/app/api/users/[id]/route.ts:1`。

- Todo 機能
  - すべて BFF の `/api/todos/**` を経由。CSRF 検証と `Authorization` 付与を Route Handler 側で実施。

---

## 良い点（ベストプラクティス準拠）

- httpOnly Cookie + BFF 経由での `Authorization` 付与
  - アクセストークンをクライアント JS から不可視化し、BFF がバックエンドへ安全に委譲する実装は堅牢です。
  - 参照: `frontend/src/app/api/auth/login/route.ts:1`、`frontend/src/app/api/todos/route.ts:1`、`frontend/src/app/api/todos/[id]/route.ts:1` など。

- CSRF トークンの発行と検証
  - `crypto/randomBytes` を使用して Node ランタイムで安全に生成し、ヘッダと Cookie の一致で検証する実装は適切です。
  - 参照: `frontend/src/app/api/auth/csrf/route.ts:1`、`frontend/src/lib/csrf-utils.ts:1`。

- ルート保護の多層防御
  - Middleware による入口ガード（トークン存在/フォーマット）と、クライアント側 `AuthGuard` による UX 寄りのガードを併用。
  - 管理機能の API はサーバ側でも is_superuser/roles を厳密に判定。
  - 参照: `frontend/src/middleware.ts:1`、`frontend/src/components/auth/auth-guard.tsx:1`、`frontend/src/app/api/users/route.ts:1`。

- 最小限で安全なロギング
  - 開発時のみ有効化され、トークン値など機微情報は出力しない方針が守られています。
  - 参照: `frontend/src/app/api/todos/route.ts:1`（devLog）、`frontend/src/hooks/use-cookie-auth-queries.ts:1`。

- セキュリティヘッダの設定
  - `X-Frame-Options: DENY`、`X-Content-Type-Options: nosniff` を付与。
  - 参照: `frontend/next.config.ts:1`。

---

## 気付いた問題点・リスクと改善提案

1) 直接バックエンド呼び出しメソッドの不整合（Cookie 認証方式と齟齬）
- 事象: `cookieApiClient.get/post/put/patch/delete` は `config.api.baseUrl` へ直接 fetch していますが、Authorization ヘッダは付与せず、httpOnly Cookie も別オリジンには送信されないため、認可に失敗します。
  - 参照: `frontend/src/lib/cookie-api-client.ts:188` 以降。
- 影響: 現行 UI では Todo 等は BFF 経由なので実害は少なそうですが、`cookieUserApi` が同設計で定義されており、将来的に誤用すると 401/CORS 関連の不具合や CSRF 未検証の経路が混在します。
- 提案: 直接バックエンドではなく、BFF の `/api/**` を常に経由するよう統一してください（例: `cookieUserApi` も `/api/users` を叩く）。未使用 API は誤使用防止のため削除/コメントアウトも検討。

2) Middleware のリダイレクト URL がクエリを保持しない
- 事象: ミドルウェアのログイン・リダイレクトで `redirect` パラメータに `pathname` のみを設定しています。
  - 参照: `frontend/src/middleware.ts:1`。
- 提案: `search`（クエリ文字列）も含めて復元できるようにし、UX を改善してください。

3) JWT フォーマット検証のみで有効期限は未考慮
- 事象: Middleware はトークンが「JWT 形式であるか」のみをチェックします（`3 ドット区切り`）。
- 提案: 厳密な検証はバックエンド側で十分ですが、UX 観点では `exp` を軽く確認し、明らかに期限切れであればログインへ誘導すると二度手間（表示→401→リダイレクト）が減ります。

4) CSRF トークン初期化の SSR フォールバック URL
- 事象: `cookieApiClient.initializeCSRFToken()` が SSR/Node 実行時に `http://localhost:3000` をフォールバックに使う可能性があります。
  - 参照: `frontend/src/lib/cookie-api-client.ts:13` 付近。
- 現状の使用箇所はクライアント限定（hooks 経由）で実害は出にくい設計ですが、念のため BFF 由来の絶対パスにするか、呼び出しをクライアント時のみ遅延実行にするなど、誤用耐性を高めると安心です。

5) Route Handler の params 型
- 事象: 動的ルートの params を `Promise<{ id: string }>` として `await` しています。
  - 参照: `frontend/src/app/api/todos/[id]/route.ts:1`、`frontend/src/app/api/users/[id]/route.ts:1`。
- 提案: Next.js 15 では `({ params }: { params: { id: string }})` の同期型が一般的です。将来のメンテ性向上のため、公式に寄せると良いです。

6) セキュリティヘッダの拡充
- 事象: 既に一部ヘッダは設定済みですが、実運用では CSP/Referrer-Policy/Permissions-Policy 等の追加が推奨です。
- 提案: 最低限、CSP の導入を検討ください（開発時は緩め、本番で厳格化）。

7) リフレッシュフローの自動化
- 事象: `/api/auth/refresh` は実装済みですが、アクセストークン期限切れ時の自動リフレッシュ連携はまだ限定的です。
- 提案: BFF 側（Route Handler）で 401 を検知した際にリフレッシュを試みる、あるいは UI 側のクエリで 401 を拾って自動で `/api/auth/refresh` を叩くなどのパターンを検討できます。

8) ルーティング定義の一貫性
- 事象: Middleware の保護対象に `/profile` `/admin` `/settings` が含まれますが、実 UI は `/dashboard/profile` 等の配下にあります。
  - 参照: `frontend/src/middleware.ts:1`、`frontend/src/components/layout/dashboard-layout.tsx:1`。
- 提案: 実態と合わせてルールを簡潔化し、将来のメンテで齟齬が出ないようにしてください（現状は `/dashboard/**` が主）。

9) `config.ts` の既定値
- 事象: `cookieAuth.enabled` の既定値が `... === 'true' || true` になっており、常に `true` になります。
  - 参照: `frontend/src/lib/config.ts:1`。
- 提案: フラグの実効性のため、`|| true` を除去してください。

---

## 詳細レビュー（ファイル別抜粋）

- ミドルウェア（保護ルート判定/リダイレクト）
  - `frontend/src/middleware.ts:1`
  - JWT 形式判定・Cookie 名の整合性は良好。リダイレクト時のクエリ引き継ぎに改善余地。

- BFF（Auth）
  - `frontend/src/app/api/auth/login/route.ts:1` `frontend/src/app/api/auth/register/route.ts:1` `frontend/src/app/api/auth/logout/route.ts:1` `frontend/src/app/api/auth/refresh/route.ts:1` `frontend/src/app/api/auth/me/route.ts:1`
  - CSRF 検証・Cookie 設定・バックエンド委譲の流れは適切。login でのレスポンス生成/クッキー設定が二重化しており、簡素化余地あり（機能上は問題なし）。

- BFF（Todos）
  - `frontend/src/app/api/todos/route.ts:1`、`frontend/src/app/api/todos/[id]/route.ts:1`
  - すべての状態変更で CSRF 検証、有効。GET も BFF 経由で Authorization を付与。

- BFF（Users：管理機能）
  - `frontend/src/app/api/users/route.ts:1`、`frontend/src/app/api/users/[id]/route.ts:1`、`frontend/src/app/api/users/me/route.ts:1`
  - `/auth/me` を呼び、`is_superuser` または `roles[].name === 'admin'` を確認してからバックエンドへ委譲しており、サーバサイドでの RBAC が担保されています。

- クライアント側ガード
  - `frontend/src/components/auth/auth-guard.tsx:1`
  - 画面遷移の UX を損なわずに未認証→ログイン誘導、ロール UI 制御が実装されています（最終的な強制は Route Handler が担保）。

- Todo 画面
  - `frontend/src/components/tasks/*`
  - React が XSS を自動エスケープするため、タイトル/説明の描画は安全側。API 例外時の通知・ローディングも適切。

- React Query 設定
  - `frontend/src/lib/react-query.tsx:1`
  - 再試行やデフォルトの stale/gc 時間など、実運用に耐える初期設定が施されています。

---

## 推奨修正（例）

- BFF 経由へ統一（誤用防止）
  - `frontend/src/lib/cookie-api-client.ts:188` 以降の `get/post/put/...` を `/api/**` に向ける、もしくは一旦削除。`cookieUserApi` も `/api/users` を利用する形に。

- Middleware のリダイレクト改善
  - `redirect` パラメータへクエリも含める（`pathname + search`）。

- 期限切れトークンの早期判定（任意）
  - ミドルウェアで JWT の `exp` を軽くデコードし、明らかに失効している場合はログインへ誘導。

- セキュリティヘッダ拡充
  - `next.config.ts` に CSP/Referrer-Policy/Permissions-Policy などを追加（本番のみ有効など環境分岐）。

- 設定値の是正
  - `frontend/src/lib/config.ts:1` の `cookieAuth.enabled` の既定値を修正。

- params 型の純化
  - 動的 Route Handler の `params` を同期型に揃える。

- CSRF トークン初期化の安全化（任意）
  - サーバ側での実行を避けるため、初期化関数の呼び出しをクライアント限定で遅延実行するか、BFF の絶対パスを使用。

---

## 追加確認事項（運用時）

- バックエンド側 CORS/CSRF 設定との整合
  - 実運用は「フロント→BFF（同一オリジン）→バックエンド（サーバ間通信）」の前提であれば、ブラウザからバックエンド直叩きは無効化で問題なし。

- HTTPS/`secure` Cookie
  - 本番は HTTPS かつ `secure: true` で運用される前提。リバースプロキシ配下での `X-Forwarded-Proto` 等の取り扱いに注意。

- トークン回転/再ログイン UX
  - アクセストークン期限切れ→自動リフレッシュ失敗時の強制ログアウト動作（Cookie クリア、ログイン画面誘導）をユーザが理解できるメッセージに。

---

## 結論

現行のフロントエンド実装は、BFF 経由の Cookie 認証・CSRF 対策・ロール判定の多層防御といった重要ポイントを押さえた、堅牢で現実的な設計です。主に「未使用の直接バックエンド呼び出しロジックの整理」「UX/保守性向上の細かな改善（リダイレクト引き継ぎ、params 型、設定既定値修正、ヘッダ拡充）」を行うことで、エンタープライズ運用に一層適した形に仕上がります。

必要であれば、上記推奨修正の具体的なパッチ適用や自動リフレッシュ連携の実装も対応可能です。ご希望をお知らせください。
