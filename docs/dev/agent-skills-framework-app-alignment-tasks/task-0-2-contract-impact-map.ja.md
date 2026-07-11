# Task 0-2: Backend API / Frontend Contract 影響マップ

作成日: 2026-07-11

## 目的

本書は、KOIKI-FW で業務アプリを構築・変更するときに Agent Skills が案内すべき backend API と frontend contract を整理する。個別 endpoint の完全な仕様書ではなく、配置・変更・検証の判断に必要な契約を対象とする。

## 1. API ownership と利用境界

| 所有者 | 代表的な範囲 | frontend との関係 | 変更時の第一 Skill |
| --- | --- | --- | --- |
| `components/libkoiki/` | auth basic / token / password / session、users、security monitor、Todo sample | reusable API contract。browser session、Cookie-CSRF、RBAC、Todo の optimistic lock は利用側へ影響する | `koiki-libkoiki-feature-work`。auth/security を含む場合は `koiki-auth-security` を併用 |
| `components/koiki_ref_app/` | SSO、SAML、business clock、reference app 固有 integration | SPA は authorization initiation と session exchange を直接利用する。IdP callback、redirect URI、ticket / code / state は browser flow に影響する | `koiki-refapp-feature-work`。SSO/SAML は `koiki-auth-security` を併用 |
| `apps/` | 案件固有 API、model、schema、service、repository、ASGI / router composition | frontend は root `frontend/` から業務 API を利用できるが、frontend を `apps/` に配置しない | `koiki-business-app-feature-work`。frontend contract に影響すれば `koiki-frontend-work`（Task 2-1 で新設）を併用 |
| root `frontend/` | Vite + React SPA、feature API、Query、route、UI、frontend test | backend API の browser consumer。API の実装 ownership は持たない | `koiki-frontend-work`（Task 2-1 で新設） |

`app/` は compatibility wrapper であり、新規 API の配置先ではない。Todo は `libkoiki` の starter/sample capability であり、業務固有 API を framework へ置く前例にはならない。

## 2. Backend API 変更時の共通確認契約

| 観点 | 必ず確認する事項 | 主な責務 |
| --- | --- | --- |
| Ownership / layering | reusable、reference-app 固有、案件固有のいずれか。API → Service → Repository → Model/Schema の依存方向を保つ | overview / backend Skill |
| Schema / response | request・response schema、required / optional field、status code、204 no-content、409 conflict、error payload を更新する。互換性を壊す変更は consumer と migration を確認する | API owner + frontend consumer |
| Authorization | UI の表示制御ではなく、backend dependency / permission / role check で必ず強制する | backend owner + auth-security |
| Cookie session / CSRF | browser session の unsafe request は backend の CSRF contract に従う。Bearer client と token-returning endpoint の互換境界を崩さない | libkoiki + auth-security + frontend |
| Configuration / deployment | Vite の `VITE_*` は公開 build-time config。Cookie、CORS、CSRF、IdP redirect URI、security header は backend / deployment 側の source of truth | backend owner + frontend + auth-security |
| Validation | 変更責務に応じた backend unit / integration、frontend API boundary / component test、必要な browser flow を追加する | testing + changed owner |

## 3. Browser session と auth contract

### Session API

browser SPA は `/api/v1/auth/session/*` を `credentials: "include"` で利用する。

- `GET /auth/session/csrf`: backend が CSRF Cookie と token / `header_name` を返す。
- `POST /auth/session/login`、`/register`: CSRF を検証し、token 値を body に返さず Cookie を backend が設定する。
- `POST /auth/session/refresh`、`/logout`: refresh Cookie を backend 側で扱い、CSRF を検証する。
- `GET /auth/session/me`: backend が認証・ユーザー有効性を確認する。frontend は認可の唯一の根拠にしない。

SSO / SAML には token-returning endpoint と Cookie session endpoint が併存する。browser SPA は `/auth/session/sso/login` と `/auth/session/saml/login` を使い、token-returning `/auth/sso/login`、`/auth/saml/login` は既存 Bearer client との互換用途として扱う。

### CSRF / authorization の不変条件

- Cookie 認証の unsafe request は backend で CSRF 検証する。Bearer 認証の API client には CSRF を要求しない。
- `ActiveUserDep` は user の active 状態を確認する。permission / SuperUser dependency は API 側で保持する。
- Todo、user 更新、business clock 更新などの Cookie 認証 unsafe API は、認証と CSRF を同時に確認する。
- SSO / SAML の authorization、callback、exchange、redirect は security-sensitive flow として扱う。

### frontend transport の標準

- `shared/api/http-client.ts` が `credentials: "include"`、CSRF 初期化、403 `CSRF_TOKEN_INVALID` 時の一度だけの retry、JSON parse、`ApiError` 正規化を担う。
- feature API は transport を直接再実装せず、`requestJson<T>()` を使う。
- Query / mutation は feature ごとの query key、cache invalidation、error handling を担い、API response を Zustand に保存しない。

## 4. SPA 固有の推奨と技術非依存の contract

| Vite + React SPA の標準実装 | 将来の別 frontend 技術にも適用する contract |
| --- | --- |
| React Router の route / layout / lazy loading | protected route は UX の補助であり、backend authorization を代替しない |
| TanStack Query の server state、feature-local query key、mutation invalidation | API response cache、更新後の再取得 / invalidation、error state を明示する |
| `CookieApiClient` の CSRF 初期化・retry | Cookie session、credentials、CSRF header、refresh / logout の backend ownership を守る |
| Vitest + Testing Library + MSW | transport、schema、error、auth / permission、mutation の代表リスクを検証する |
| `VITE_*` と Vite build | browser に公開する値と backend secret / security setting を分離する |

## 5. 代表シナリオと期待 Skill routing

| シナリオ | 主な確認事項 | 期待 Skill |
| --- | --- | --- |
| `apps/` に業務 API を追加 | ownership、ASGI / router composition、schema、migration、auth、frontend consumer の有無 | `koiki-business-app-feature-work`。frontend consumer を追加・変更する場合は `koiki-frontend-work`、test は `koiki-testing` |
| reusable framework API を追加 | reusable 性、reference app / browser consumer の互換性、service-layer、integration test | `koiki-libkoiki-feature-work`。auth を含めば `koiki-auth-security`、frontend consumer があれば `koiki-frontend-work` |
| reference app API を追加 | `components/koiki_ref_app/` ownership、既存 framework composition、frontend contract | `koiki-refapp-feature-work`。auth / IdP を含めば `koiki-auth-security` |
| session auth / CSRF を変更 | Cookie / Bearer 境界、unsafe request、refresh、logout、browser failure flow、integration test | `koiki-auth-security` + `koiki-libkoiki-feature-work`。browser client を変える場合は `koiki-frontend-work` |
| SSO / SAML を変更 | redirect allowlist、state / nonce / RelayState、ticket / code exchange、Cookie session、IdP failure flow | `koiki-auth-security` + `koiki-refapp-feature-work`。callback UI を変える場合は `koiki-frontend-work` |
| root frontend の画面・API client を変更 | feature API、Query、CSRF、route、form、frontend test。backend API を実装しない | `koiki-frontend-work` |
| frontend 影響を伴う API schema 変更 | request / response、status / error、cache invalidation、form validation、consumer test | API owner Skill + `koiki-frontend-work` + `koiki-testing` |
| API ownership が未確定 | reusable / reference / business の分類後に実装 Skill を選ぶ | `koiki-project-overview` |

## 6. 現行実装から得た Skill guidance 上の注意点

1. `SessionLoginRequest` は `email` または `username` と `password` を受ける。frontend が email login を選ぶことは current SPA の実装方針であり、backend schema 変更時は browser form と互換性を確認する。
2. `CSRFTokenResponse` は `header_name` を返す一方、current `CookieApiClient` は `x-csrf-token` を固定で送る。CSRF header 名を設定変更する場合は、frontend transport と test を同時に変更する必要がある。
3. Todo update は optimistic-lock `version` を必須とし、競合時は 409 を返す。frontend は current version を送信し、409 を利用者へ再確認として扱う。これは API schema / error / mutation contract を同時に変える代表例である。
4. `features/users/api.ts` は `requestJson<T>()` ではなく raw `Response` を返す既存実装である。新規 frontend API は standard transport / typed feature API に従い、既存 user client の整理は別の frontend implementation task として扱う。
5. `apps/README.md` は root `frontend/` を標準配置と明記している。業務 API の追加は frontend directory を `apps/` に作る根拠にならない。

## 7. Task 1-1 / Task 2-1 への反映方針

- backend Skills には、schema / status / error、authorization、Cookie-CSRF、config、migration、test、frontend contract の影響確認を、責務に応じて追加する。
- `koiki-auth-security` は session Cookie / CSRF、Bearer compatibility、SSO/SAML browser exchange を明示する。
- `koiki-testing` は backend API contract、frontend transport / Query、browser flow の最小テスト選択を明示する。
- `koiki-frontend-work` は root `frontend/` の Vite + React SPA 標準と、上記の技術非依存 contract を区別して案内する。
- `future-role-alignment.md` は `apps/<project-slug>/frontend/` を前提としない方針へ更新する。
