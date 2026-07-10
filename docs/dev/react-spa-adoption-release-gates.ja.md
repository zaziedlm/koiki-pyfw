# React SPA 採用・配備ゲート

最終更新: 2026-07-10

## 目的と適用範囲

この文書は、Vite + React SPA を参照実装から採用対象の frontend として扱うとき、および production 配備前に満たすべき判断・確認事項を定義する。

これは実装タスクやデプロイ手順そのものではない。各ゲートの証跡を残し、未完了の項目を受容したまま CI 有効化や production 配備を進めないためのチェックリストである。

現行構成、実装規約、移行完了範囲は `docs/dev/react-spa-migration-completion.ja.md` を参照する。

## 1. Frontend CI 採用方針

### 方針

- 現在の `dev/v0.7-react-only` では、frontend CI は有効化しない。既存 workflow の対象ブランチと、SPA の採用判断を混在させないためである。
- React SPA を採用対象にする `dev/v0.8` 以降のブランチでは、frontend を変更する pull request に frontend checks を必須とする。
- 有効化時は `.github/workflows/frontend-ci.dev-v0.8.yml.disabled` を単に rename するか、既存 `.github/workflows/ci.yml` に統合する。どちらを採る場合も、対象 branch、required check 名、Node version を PR 前に確定する。
- frontend が将来差し替え可能な参照実装であることは、採用済みの SPA に対する回帰検証を省略する理由にはしない。別 stack を導入する場合は、その stack 用の独立した CI contract を定義する。

### 必須 checks

frontend CI は `frontend/` を working directory とし、次を順に実行する。

1. `npm ci`
2. `npm run check-types`
3. `npm run lint`
4. `npm test`
5. `npm run build`

Node.js は template の `22` を基準にする。React Router v8 を検討する場合は、必要な Node engine を先に確認し、CI baseline と lockfile を同じ change で更新する。

### 有効化完了条件

- workflow が `.yml` として有効で、採用対象 branch の push と pull request で発火する。
- repository branch protection で frontend check が required になっている、または required にしない理由と代替統制が release record に記録されている。
- 初回 Actions 実行が、上記5 checks すべて成功している。
- frontend CI が backend CI の Python / DB job を不要に重複させない。

## 2. Production 配備ゲート

### 2.1 Build と配信

- production image は `FRONTEND_BUILD_ENV_FILE=.env.production`、または同等の明示した build input で作成する。
- `VITE_API_BASE_URL` は同一 origin 配備なら `/api/v1` とする。別 origin を採る場合は、CORS、Cookie `SameSite` / `Secure`、CSRF transport を一組の設計としてレビューする。
- 静的 SPA が nginx の `/health` で応答し、任意の React Router deep link が `/index.html` fallback で表示できる。
- production 用 image tag / digest、frontend build input、backend version を deployment record に残す。

### 2.2 Backend 設定と秘密情報

- `APP_ENV=production` と `ENVIRONMENT=production` を明示し、起動ログで development 扱いになっていないことを確認する。
- `JWT_SECRET` と `AUTH_CSRF_SECRET` に placeholder や development 値を使わない。HS256 用 `JWT_SECRET` は32バイト以上のランダム値にする。
- `AUTH_COOKIE_SECURE=true` を確認する。production HTTPS 配備で false を受容しない。
- Cookie domain / path / SameSite と frontend origin が意図した配備トポロジーに一致することを確認する。
- Vite の `VITE_*` は browser に公開される build-time 値である。secret や backend 内部 URL を含めない。

### 2.3 ネットワークと HTTP security

- HTTPS 終端、SPA origin、API origin、ALB / reverse proxy の route を明示する。
- 同一 origin 配備を優先する。CORS を有効にする場合は許可 origin を具体値で列挙し、`allow_credentials=True` と wildcard origin を併用しない。
- nginx の CSP、`X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy` が production response に存在することを確認する。
- Redis 分散 rate limit や trusted proxy に基づく client IP は、規模・WAF・認証試行統制の必要性が生じた時点で別途設計する。現行の小規模 ECS 前提では memory limiter の制約を deployment record に受容事項として残す。

### 2.4 IdP と browser flow

- IdP 側に production callback URI を登録し、backend の `SSO_ALLOWED_REDIRECT_URIS`、`SAML_ALLOWED_REDIRECT_URIS`、必要な default redirect URI と一致させる。
- 実 IdP で SSO と SAML の happy path を各1回以上確認する。callback、session Cookie 発行、`/session/me`、ログアウトまでを含める。
- password login について、CSRF token 取得、login、protected route、Todo の create/update/delete、refresh、logout を browser で確認する。
- Cookie 認証の unsafe request を CSRF header なしで送った場合に拒否されることを確認する。

## 3. 判定と証跡

各 gate は deployment record または release issue に、少なくとも次を残す。

| 項目 | 記録する内容 |
|---|---|
| 実施日・担当 | 実施日時、担当者、環境 |
| build | image tag / digest、commit、使用した frontend build env |
| CI | workflow run URL または実行ログ、5 checks の結果 |
| 設定 | secret を露出しない形で、production 値確認済みであること |
| browser flow | 実施した login / CRUD / refresh / logout / SSO / SAML と結果 |
| 受容事項 | 未実施項目、リスク、受容者、再検討条件 |
| rollback | 前バージョン image と、切戻し判断者・手順への参照 |

## 4. ゲートを通過できない場合

次のいずれかが未確認なら、production 配備は承認しない。

- production secret や HTTPS / Cookie Secure の確認が取れていない。
- SPA/API origin と Cookie / CORS 設定の整合が取れていない。
- 実 IdP を使う対象なのに SSO または SAML callback を確認していない。
- 採用対象 branch の frontend CI が必須化されていない、かつ代替統制も記録されていない。

E2E 自動化（Playwright）は、この gate の browser 確認を恒久的に代替するための後続候補である。導入までは、上記の手動確認と証跡を必須とする。
