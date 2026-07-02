# KOIKI-FW v0.7 Frontend SPA Migration Plan

## 目的

この文書は、現行 `frontend/` の Next.js 実装を、より単純な React SPA へ置き換えるための移行計画を定義する。

この frontend は、次の機能を示す参照実装である。

- パスワードログインとユーザー登録
- SSO ログイン
- SAML ログイン
- access token / refresh token に基づく認証
- Todo CRUD

目的は、現在 Next.js route handler で担保しているセキュリティ特性を維持しながら、frontend framework 由来の複雑さを下げることである。

## 決定事項サマリ

目標アーキテクチャは次の通り。

- `frontend/` は Vite + React + TypeScript の SPA とする。
- browser-side routing は React Router が担う。
- 認証 Cookie、CSRF 検証、token refresh、logout、SSO token exchange、SAML ticket exchange は FastAPI が担う。
- SPA は access token / refresh token を browser storage に保存しない。
- SPA は backend API を `credentials: "include"` 付きで呼び出す。
- state-changing request では `x-csrf-token` header を送る。
- backend parity が揃った後に、Next.js route handler と middleware を削除する。

## 関係者向け説明サマリ

この移行は、現在の参照 frontend から Next.js を外すためだけの判断ではない。より重要なアーキテクチャ上の判断は、特定の frontend framework に依存しない認証境界を確立することである。

KOIKI-FW は、認証、token lifecycle、CSRF、SSO、SAML の振る舞いを backend 側で主導するべきである。frontend 実装は、security-sensitive behavior を再実装したり proxy したりするのではなく、明確な contract を利用する。

これにより、同時に次の 2 つを実現できる。

1. 現在の参照 frontend を単純な React SPA にできる
2. 将来、顧客固有の Next.js frontend が必要になった場合でも、より整理された実装にできる

将来顧客要件として Next.js が必要になった場合、Next.js は主に UI、routing、SSR/RSC、caching、deployment integration を担うべきである。token 発行、refresh token rotation、CSRF 検証、SSO exchange、SAML ticket exchange の owner にはしない。

## 現行 Next.js 実装の問題点

現行 `frontend/` 実装では、Next.js を frontend framework と backend-for-frontend の両方として使っている。この構造には複数の問題がある。

### Security-Sensitive Behavior が分散している

認証の振る舞いが FastAPI と Next.js route handler に分散している。現状 Next.js layer は次の処理に関与している。

- access token cookie 発行
- refresh token cookie 発行と rotation
- logout 時の cookie clear
- CSRF token 生成と検証
- SSO authorization / login exchange proxy
- SAML authorization / login ticket exchange proxy
- 認証付き Todo / User API proxy

このため、認証処理の真の owner を特定しにくい。また、token や SSO/SAML の振る舞いを変更するたびに、security review が必要な場所が増える。

### Frontend Framework の選択が認証設計に影響している

auth cookie、refresh behavior、CSRF behavior が Next.js route handler の中に実装されているため、参照 frontend を変更するだけでも security-sensitive logic の移動が必要になる。

これは framework coupling の問題である。参照アプリケーションは、backend authentication model を再定義せずに、React SPA、Next.js、その他 frontend の間で切り替えられるべきである。

### BFF Proxy Logic が backend concern を重複している

現行 Next.js route handler の多くは FastAPI へ request を転送しているが、同時に token extraction、response shaping、cookie handling、CSRF check、一部 authorization check も追加している。これにより、実 backend API と整合させ続ける必要のある第 2 の API surface が生まれている。

特に次の領域では重複がリスクになる。

- error response shape
- token expiry と refresh failure behavior
- Cookie attributes
- CSRF failure handling
- SSO/SAML callback edge cases

### 参照 Frontend が目的に対して複雑になっている

frontend の目的は、login、SSO/SAML、token management、Todo behavior を示すことである。現行 Next.js 実装は、framework-specific な server behavior を追加しており、参照すべき flow を見えにくくしている。

starter/reference frontend として有用なのは、次の点を示すことである。

- browser が login を開始する方法
- browser が authenticated API を呼ぶ方法
- CSRF を付与する方法
- callback page が SSO/SAML flow を完了する方法
- 認証後に Todo CRUD が動作する方法

これらの flow に Next.js 固有の server infrastructure は必須ではない。

## Backend 主導の対処方針

対処方針は、security-sensitive boundary を FastAPI 側へ移し、frontend が安定した contract として利用する形にすることである。

FastAPI が担うべきもの:

- password login / registration における token issuance
- access token cookie 発行
- refresh token cookie 発行と rotation
- logout と token revocation
- auth cookie clearing
- CSRF token 発行と検証
- Cookie credentials からの current-user resolution
- SSO authorization code exchange
- SAML login ticket exchange
- security logging と audit behavior

frontend が担うべきもの:

- UI state
- browser routing
- forms
- `credentials: "include"` による backend API 呼び出し
- state-changing request への CSRF header 付与
- PKCE verifier、OIDC state/nonce、SAML RelayState など、一時的で公開可能な flow correlation data の保持

これにより、backend が security behavior の source of truth となり、frontend 実装は置き換え可能になる。

## React SPA 参照実装の位置づけ

目標とする参照実装は Vite + React + TypeScript の SPA である。理由は、frontend contract を最も framework-specific machinery が少ない形で示せるためである。

SPA は意図的に単純にする。

- server-side frontend runtime を持たない
- frontend-owned token storage を持たない
- backend 呼び出し以外の frontend-owned token refresh 実装を持たない
- Next.js route handler を持たない
- auth proxy layer を持たない
- 小さな API client から backend API を直接呼ぶ
- browser route は React Router が担う
- request state と cache invalidation は React Query が担う

この参照実装は、KOIKI-FW の backend auth contract が plain browser application から利用可能であることを示す。contract が明確になれば、Next.js frontend も同じ contract を、より薄く、review しやすい形で利用できる。

## 将来の Next.js 互換性

将来、顧客要件で Next.js が必要になった場合でも、推奨アーキテクチャは現行の BFF-heavy design へ戻すことではない。

Next.js に推奨する役割:

- page routing
- layout と UI composition
- product value がある場合の SSR / RSC
- metadata と cache behavior
- deployment 上必要な場合のみ、薄い same-origin facade

Next.js で避けるべきもの:

- access token / refresh token の発行
- refresh token rotation
- SSO / SAML assertion の検証
- CSRF validation の source of truth になること
- backend authorization rule の重複実装
- token value を browser-accessible storage に保存すること

この model では、Next.js は server component や route handler から FastAPI を呼んでもよい。ただし、その呼び出しは backend auth contract へ委譲するものであり、Next.js 自身が auth behavior を実装するものではない。

## React Server Components を採用しない理由

React Server Components は、この repository における Next.js の単純な代替ではない。RSC には server runtime integration、routing convention、bundler support が必要である。Next.js を外しつつ RSC を維持しようとすると、新しい server-side frontend architecture を追加することになり、この参照アプリケーションを単純化できない。

今回意図している単純化は、security-sensitive behavior を FastAPI backend が担い、frontend は browser-only React SPA とすることである。

## 現行 Frontend の責務

現行 `frontend/` 実装には、2 種類の concern が含まれている。

UI concern:

- public landing page
- login / registration screen
- SSO / SAML callback screen
- authenticated dashboard
- Todo CRUD screen
- shared UI components, hooks, types

Next.js により実装されている server/BFF concern:

- authentication cookie issuance
- refresh token cookie rotation
- logout cookie clearing
- CSRF token generation and validation
- authenticated Todo / User API proxying
- SSO authorization proxying
- SSO login code exchange proxying
- SAML authorization proxying
- SAML login ticket exchange proxying
- protected route middleware

移行では、UI concern は React に残し、BFF concern は FastAPI へ移す。

## Target Security Model

### Token Storage

Access token と refresh token は、`localStorage`、`sessionStorage`、IndexedDB、non-httpOnly cookie に保存してはならない。

FastAPI は次を発行する。

- access token cookie
- refresh token cookie
- CSRF token cookie または CSRF response payload。最終的な backend 実装に合わせて決める

認証 Cookie には次の属性を設定する。

- `HttpOnly`
- production では `Secure`
- default は `SameSite=Lax`。cross-site deployment が必要な場合のみ `None`
- `Path=/`
- 文書化された deployment reason がない限り、広い `Domain` 属性は付けない

production HTTPS と host 制約が許す場合は、auth cookie に `__Host-` prefix を使うことを優先する。

### CSRF

browser cookie は自動送信されるため、cookie-authenticated state change には CSRF protection が必要である。

Backend requirements:

- `POST`, `PUT`, `PATCH`, `DELETE` で CSRF を検証する
- safe `GET` request では CSRF を要求しない
- CSRF token がない、または不正な場合は安定した error code で拒否する
- login / refresh 時に必要に応じて CSRF token を rotate または reissue する
- raw CSRF token value をログに出さない

Frontend requirements:

- 必要に応じて state-changing operation の前に CSRF bootstrap endpoint を呼ぶ
- 現在の CSRF token を設定済み header にコピーする
- backend が対応している場合のみ、既知の CSRF refresh failure に対して 1 回だけ retry する

### CORS And Deployment

SPA と API が異なる origin で配信される場合:

- backend CORS は明示的な frontend origin のみ許可する
- `Access-Control-Allow-Credentials` を有効にする
- credentialed request では wildcard origin を使わない
- Cookie の `SameSite` と `Secure` 設定は deployment model と一致させる

SPA と API が同一 origin で配信される場合:

- same-origin API path を優先する
- CORS は無効または最小にする
- Cookie は host-only にする

### SSO And SAML

frontend が保持してよいのは、一時的で公開可能な flow state のみである。

- OIDC PKCE code verifier
- OIDC state / nonce correlation material
- SAML RelayState correlation material
- callback redirect target

Backend が担うべきもの:

- authorization code exchange
- SAML ticket exchange
- token pair creation
- cookie issuance
- SAML response validation
- RelayState / ticket expiration validation
- audit and security logging

## Scope

In scope:

- `frontend/` に Vite React SPA replacement を作る
- React page / component を Next.js API から移行する
- 現行 Next.js auth/proxy behavior を FastAPI へ移す
- Docker と local development docs を更新する
- frontend environment variable 名を更新する
- security-sensitive path の validation と test coverage を更新する

Out of scope:

- backend auth domain model の再設計
- Keycloak や SAML provider behavior の置き換え
- production-grade design system の作成
- 現行 reference flow を超える新しい business feature の追加
- 別 meta-framework を使った frontend の RSC 化

## Backend Placement Rules

repository boundary guidance に従う。

- reusable な auth、cookie、CSRF、token、middleware、framework behavior は `components/libkoiki/` に置く
- current reference application の SSO/SAML wiring は `components/koiki_ref_app/` に置く
- root `app/` は、明示的に legacy import を維持する場合を除き compatibility wrapper として扱う

Todo は `libkoiki` の starter/sample capability として扱う。新しい project-specific API behavior を `libkoiki` に置く前例として Todo API を使ってはならない。

## Migration Strategy

認証 behavior を途中で壊さないように、移行は段階的に進める。

1. Inventory and contract definition
2. Backend cookie-auth parity
3. Frontend SPA scaffold and API client replacement
4. Page and callback migration
5. Next.js removal
6. Docker, docs, and validation

backend endpoint が同等の behavior を提供し、security-sensitive path が test で覆われるまでは、Next.js route handler を削除しない。

## Task Directory

詳細な task instruction は次に置く。

- `docs/dev/v0.7-frontend-spa-migration/`

推奨実行順:

1. `task-0-1.md` - frontend responsibility inventory
2. `task-0-2.md` - backend auth contract design
3. `task-1-1.md` - backend cookie and CSRF primitives
4. `task-1-2.md` - password auth cookie endpoints
5. `task-1-3.md` - SSO and SAML cookie endpoints
6. `task-1-4.md` - backend integration tests
7. `task-2-1.md` - Vite React scaffold
8. `task-2-2.md` - SPA API client and auth hooks
9. `task-2-3.md` - route and page migration
10. `task-2-4.md` - SSO/SAML callback migration
11. `task-3-1.md` - remove Next.js server surface
12. `task-3-2.md` - Docker and environment migration
13. `task-4-1.md` - final validation and release notes

## Validation Standard

移行完了とみなす前に、最低限次を確認する。

- backend tests が login、refresh、logout、CSRF behavior を証明している
- backend tests が SSO / SAML exchange endpoint による Cookie 発行を証明している
- backend tests が state-changing request における invalid CSRF rejection を証明している
- frontend typecheck が通る
- frontend production build が通る
- Docker frontend service が起動し healthcheck が通る
- manual または automated flow で login -> Todo CRUD -> logout が証明されている
- configured local environment で SSO / SAML happy path が検証されている

## Open Questions

- production deployment では SPA と API を same origin で配信するべきか
- auth cookie は現行 `koiki_*` 名を使うか、compatibility window を設けて `__Host-*` 名へ移行するか
- CSRF は synchronizer-token based と signed double-submit cookie based のどちらにするか
- どの SSO/SAML callback URL を backward compatible として維持する必要があるか
- 旧 Next.js 実装は 1 branch で削除するか、短期間 fallback branch として残すか

## Change Control

この計画を変更する場合、execution order、scope、completion criteria に影響する変更であれば、同じ change window で `docs/dev/v0.7-frontend-spa-migration/` 配下の task instruction も更新する。

英語版 `docs/dev/frontend-spa-migration-plan.md` とこの日本語版は同期対象である。一方を更新した場合は、もう一方も確認し、必要に応じて同じ change window で更新する。
