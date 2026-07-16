# Frontend SPA 移行計画・タスクの点検報告

点検日: 2026-07-04

## 点検の前提

[frontend-spa-migration-plan.md](./frontend-spa-migration-plan.md)(および [frontend-spa-migration-plan.ja.md](./frontend-spa-migration-plan.ja.md))と
[v0.7-frontend-spa-migration/](./v0.7-frontend-spa-migration/) 配下の全13タスクを、現行の `frontend/`(Next.js 15 / React 19)と
backend(`components/libkoiki/`・`components/koiki_ref_app/`)の実装と突き合わせて点検した。
本報告は指摘の記録であり、計画ファイル・タスクファイル自体への反映は別途の変更ウィンドウで行う。

事実確認の結果、計画の現状認識は概ね正確:

- API route handler は計画どおり **正確に16件**(`/api/health` 含む)
- トークンは httpOnly cookie(`koiki_access_token` / `koiki_refresh_token`)のみで、browser storage には SSO/SAML のフロー相関データ(state/nonce/PKCE verifier/RelayState)と UI 設定しか置いていない
- 対象ページ7ルートは計画のリストと完全一致
- refresh token の rotation / 失効(`is_revoked`)は backend に実装済み
- CORS は `allow_credentials=True` 設定済み(origins は env 依存)
- SAML の ACS(IdP からの POST)は既に backend 側に着地し、login ticket 付きで frontend へ 303 redirect する構成
- 日英計画書のセクション構成は同期している

以下、指摘事項を重要度順に記載する。

---

## 重要度: 高(設計判断の欠落・セキュリティ関連)

### 1. Users API の認可 parity がタスクに存在しない(実質的なセキュリティ後退リスク)

現行 Next.js BFF は `/api/users` GET/POST に **admin ロールチェックを実装**している(`frontend/src/app/api/users/route.ts`)。一方 backend 側は:

- `GET /api/v1/users`(一覧): `has_permission("read:users")` あり
- `POST /api/v1/users`(作成): **認可チェックなし**。`components/libkoiki/src/libkoiki/api/v1/endpoints/users.py` で `SuperUserDep` がコメントアウトされており、意図的に「誰でも作成可」のサンプル状態

BFF 削除後、ユーザー作成の実効ポリシーが「admin のみ」→「認証不要」に緩む。計画本文は「BFF の一部認可チェック」をリスクとして言及しているが、**どのタスクにも Users API の認可 parity 確認が含まれていない**(task-2-2 の対象は auth/todo フックのみ、task-0-1 の分類頼み)。task-0-2 または task-1-x に「BFF が実装している認可チェックの backend 側 parity 確認」を明示すべき。

### 2. 既存 API 契約(JSON token body)との互換方針が未決

現行 backend の login/refresh/SSO login/SAML login はすべて **JSON body で token pair を返す**(`TokenWithRefresh`)。Cookie 発行への移行で:

- 既存エンドポイントを Cookie 発行に「変更」するのか、Cookie 用エンドポイントを「新設」するのか
- JSON body での token 返却を残すのか(既存 integration test `test_auth_api.py` は body の token を assert している。Bearer 利用の非ブラウザクライアントも壊れる)
- 併存させる場合の切替方法(ヘッダ/クエリ/別パス)

がどのタスクにも現れない。これは task-1-1〜1-3 全体の実装形を左右する最重要の設計判断であり、task-0-2 の成果物として明示すべき。

### 3. CSRF 検証のスコープが Bearer クライアントを壊しうる

計画の backend 要件は「POST / PUT / PATCH / DELETE で CSRF を検証」と無条件に書かれているが、そのまま middleware 化すると **Authorization: Bearer で認証する既存クライアント(および既存テスト)がすべて CSRF エラーになる**。CSRF 要求は「Cookie 認証されたリクエストに限定」する必要がある。計画本文の prose(「cookie-authenticated state changes require CSRF」)と要件箇条書きが不整合。task-1-1 step 5 にスコープ規定を追加すべき。

### 4. CSRF 方式とオリジン構成の決定が連動しているのに独立した Open Question になっている

現行 CSRF は double-submit(`koiki_csrf_token` を **httpOnly:false** で発行し `x-csrf-token` ヘッダと突合)。この方式は **SPA と API が別オリジンだと成立しない**(SPA の JS は他オリジンの cookie を読めない)。クロスオリジン構成なら:

- CSRF token は response body(bootstrap endpoint の JSON)で渡す方式が必要
- auth cookie は `SameSite=None; Secure` が必須(Lax はクロスサイト fetch で送信されない)
- `__Host-` prefix も Secure 必須のため http://localhost 開発では使えない(env 分岐が必要)

Open Questions では「same-origin か」「CSRF 方式」「cookie 名」が独立した質問として並んでいるが、実際には 1 つの決定木。さらに task-3-2 step 2 が「静的配信か backend 同一配信か決める」と **Stage 3 で再度決めることになっており**、task-0-2 の成果物(CORS / same-origin 方針)と二重化している。オリジン構成は task-0-2 で確定し、task-3-2 はその決定を消費するだけにすべき。

---

## 重要度: 中(タスク記述と現状実装の齟齬・記載不足)

### 5. logout のトークン失効は「parity」ではなく新規挙動

現行 backend logout(`auth_basic.py`)は refresh token を失効せず、メッセージを返すのみ(コメントで「JWT は stateless、クライアントが破棄せよ」と明記)。Next.js 側 logout も cookie を消すだけ。task-1-2 step 5「backend token 失効と Cookie clear」は正しい目標だが **新規実装**であり、失効範囲(当該 refresh token のみか `revoke-all-tokens` 相当か)の仕様決定が必要。「parity 確認後に削除」という計画の枠組みに対し、ここは parity ではなく強化である点を明示すべき。

### 6. register の Cookie 発行判断に材料がない

現行 backend register は token を返さない(message + user のみ)。Next.js route の「token があれば cookie 設定」は実質デッドコードで、現在は登録後に再ログインが必要。task-1-2 step 2「contract に合わせる」は auto-login 化(新規挙動)かどうかの判断が前提になるが、その判断がどこにも記録されない。task-0-2 の contract 表で決めるべき。

### 7. トークン有効期限と Cookie Max-Age の不整合が既に存在する

- backend `ACCESS_TOKEN_EXPIRE_MINUTES = 60` に対し、Next.js の access cookie は maxAge **30分**
- refresh rotation は `settings.REFRESH_TOKEN_EXPIRE_DAYS` ではなく `create_expires_at(days=7)` を **ハードコード**(`auth_service.py`)

Cookie Max-Age の source of truth(JWT exp と一致させるか)を task-1-1 で決めないと、不整合を新実装に持ち込む。backend の config には cookie 関連設定が現状ゼロ(`SECURE_COOKIES` 等なし)なので、設定追加も net-new 作業として認識すべき。

### 8. login の request contract(Content-Type)が contract 候補から漏れている

既存 login は `OAuth2PasswordRequestForm`(form-urlencoded、`username` フィールド)で、Next.js が JSON の email → form の username に変換している。SPA 直呼びにする際、JSON 化するか form のままにするかは task-0-2 の contract 候補一覧に現れない。CSRF 検証との組合せ(form POST は CSRF 攻撃の典型経路)にも関わるため明記すべき。

### 9. rate limit / LoginSecurityService の維持が明記されていない

既存 login エンドポイントは slowapi の `10/minute` に加え、`LoginSecurityService`(lockout → 429 + Retry-After、progressive delay、attempt 記録)と `security_logger` / `security_metrics` のパイプラインを通る。エンドポイントを新設する場合はこの適用漏れが起きやすい。task-1-2 / 1-3 に「既存の rate limit・login security・security logging パイプラインの維持」を明示すべき(現状は auth-security.md の一般則頼み)。

### 10. `docker-compose.unified.yml` が task-3-2 の対象から漏れている

task-3-2 の対象は `docker-compose.yml` と `frontend/Dockerfile.unified` 等のみだが、リポジトリには `docker-compose.unified.yml`(dev / optimized / prod / prod-external プロファイル)があり、各プロファイルに `frontend-*` サービス(Next.js 前提、port 3000、healthcheck)が定義されている。これらも更新対象。

### 11. env 移行は「NEXT_PUBLIC_ → VITE_ の rename」では済まない

現行 env は約18種。行き先は3分類になる:

- **VITE_ へ**: API base URL、APP_NAME 等のクライアント設定
- **backend 設定へ(net-new)**: `NEXT_PUBLIC_COOKIE_SAMESITE` / `COOKIE_SECURE` / `ACCESS_TOKEN_NAME` / `REFRESH_TOKEN_NAME`(cookie 属性・名前は発行者である FastAPI 側の設定になる)、`NEXT_PUBLIC_ALLOWED_ORIGINS`(→ `BACKEND_CORS_ORIGINS` / Origin 検証)
- **削除**: `BACKEND_API_URL` / `BACKEND_API_PREFIX` 等の server-only 変数

task-2-2 step 1 / task-3-2 step 4 は単純置換の書きぶり。env → (VITE_ / backend 設定 / 削除) のマッピング表を task-0-2 か task-3-2 の成果物に加えるべき。なお API base URL の解決ロジックは現状 **3系統**(`cookie-utils.ts` / `config.ts` / SAML route 内 inline)あり、task-2-2 step 2 の統合対象として明記する価値がある。

### 12. SSO/SAML integration test のコストが1行で片付けられている

SSO / SAML は現在 **unit test のみで integration test はゼロ**。SSO exchange の integration test は外部 IdP(token endpoint / JWKS / ID token 検証)のモック戦略が必要で、task-1-4 step 7-8 の記述だけでは見積り不足になりやすい。モック方針(respx 等での IdP スタブか、service 層の境界でのスタブか)を task-1-4 に書き足すべき。

---

## 重要度: 低(移植時の注意・改善提案)

13. **認証状態判定の方式変化が未記載**: middleware.ts は httpOnly cookie をサーバー側で読んで redirect していたが、SPA は cookie を一切読めないため、認証状態は `/auth/me` の結果でしか判定できない。route guard の実装方式、初期ロード時のローディング UX、401 → refresh → retry の interceptor 相当を task-2-2 / 2-3 に明示すると漏れがなくなる。
14. **next/font と metadata の移行項目がない**: `layout.tsx` は `next/font/google`(Geist / Geist_Mono)と `metadata` export を使用。Vite ではローカルフォント or fontsource への置換、`index.html` への title/meta 移設が必要だが、task-2-1 / 2-3 / 3-1 のどこにも現れない。
15. **middleware が守る `/profile` `/admin` `/settings` にページが存在しない**: guard 移植時に「実在しない保護ルート」を引き継がないよう対象整理が必要。
16. **task-2-1 の前提条件が過剰に直列**: 「task-1-4 完了」を前提にしているが、Vite scaffold 自体は backend parity と独立して進められる。安全性の意図(Next.js 削除は parity 後)は task-3-1 の前提で担保されており、Stage 1 と task-2-1/2-3 の一部は並行可能。
17. **`use-saml-login` が hooks barrel(`hooks/index.ts`)未掲載**: 直接 import されており、移植時の漏れに注意。
18. **Tailwind v4 の Vite 対応**: 現在 `@tailwindcss/postcss` を使用。Vite では `@tailwindcss/vite` プラグインが推奨。task-2-1 step 4 に含意されるが明記推奨。
19. **frontend にテスト基盤なし(確認済み)**: 計画の frontend 検証が typecheck + build + 手動である前提は現状と一致。auth-security.md の「複数検証角度」は backend integration test で補う構図なので、指摘 12 の充実度が実質的な安全網になる。
20. **`docs/agent/app.md` が `main.py` を参照しているが実体は `app_factory.py` + `asgi.py`**: 計画の問題ではないが、task 実施中に混乱しうる既知の stale 記述。

---

## 総評

計画の現状分析(16 route handler、cookie 名、storage 利用、ページ構成)は実装と正確に一致しており、「backend 主導の認証境界確立 → SPA 化 → Next.js 削除」という段階構成・削除ゲート(parity 確認前に削除しない)も妥当。SAML ACS が既に backend 着地である点、rotation/失効・rate limit・login security が実装済みである点は、計画が想定するより Stage 1 の土台が整っていることを意味する。

一方で、**「何を決めてから作るか」が弱い**。特に (a) 既存 JSON token 契約との互換方針、(b) CSRF 方式とオリジン構成の連動決定、(c) CSRF 検証の適用スコープ、(d) Users API の認可 parity の4点は、task-1-1 着手前(task-0-2)に確定しないと手戻りかセキュリティ後退につながる。タスク粒度の指摘(5〜12)は各タスクファイルへの追記で解消できる。

## 反映時の注意

指摘を計画へ反映する場合は、`frontend-spa-migration-plan.md` / `frontend-spa-migration-plan.ja.md` と該当 task ファイルを同一変更ウィンドウで更新する(計画の Change Control 節の規約どおり)。
