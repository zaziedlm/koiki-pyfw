# React 化プランタスク点検指摘

## 目的

この文書は、`docs/dev/frontend-review-antigravity.md` と
`docs/dev/frontend-spa-migration-plan-review-ClaudeCode.ja.md` の点検内容を確認し、
現行の frontend SPA migration plan / task へ反映すべきもの、設計判断として保留すべきもの、
そのまま反映しない方がよいものを整理した記録である。

この文書では、計画書・タスク指示書への変更は行わない。

## 総評

2つのレビュー報告はかなり有用である。特に Claude Code 側は現行 backend 実装との突き合わせが深く、
`task-0-2` 着手前に反映方針を決めた方がよい指摘が複数ある。

一方で、Antigravity の一部指摘は「そのまま実装方針にする」と危ないため、
設計判断事項として扱うのが妥当である。

## 反映すべきもの

### 既存 JSON token response との互換方針

`TokenWithRefresh` を既存 endpoint から消すのか、Cookie 用 endpoint を新設するのかを
`task-0-2` で明示すべきである。

Antigravity は「body から token を消すべき」と指摘している。この方向性は browser 向けには正しいが、
既存 Bearer client / tests を壊すため、Claude Code の指摘どおり互換方針が先である。

### Cookie 認証対応 dependency

`get_user_from_token` / `ActiveUserDep` 系が Cookie から access token を読めないと、
Todo/User API が SPA から動かない。

`task-1-1` または `task-1-2` に明記すべきである。

### CSRF 適用範囲

「全 `POST` / `PUT` / `PATCH` / `DELETE`」ではなく、
「Cookie 認証された state-changing request」に限定する必要がある。

Bearer client を壊さないため、これは高優先で plan / `task-1-1` に反映対象である。

### origin 構成と CSRF 方式の連動

same-origin / cross-origin、CSRF token を cookie から読むか response body で渡すか、
`SameSite` / `Secure` / `__Host-*` の可否は独立に決められない。

`task-0-2` の contract 成果物に決定木として入れるのがよい。

### Users API の認可 parity

現行 Next BFF は `/api/users` POST を admin only にしているが、
backend `POST /users` は認証なし作成可能である。

BFF 削除で権限が緩むため、`task-0-1` / `task-0-2` / backend task のどこかに
parity 確認を追加すべきである。

### refresh endpoint の Cookie 化

`refresh_token` body input から `HttpOnly Cookie` input へ変わるため、
`task-1-2` に request body 廃止または Cookie 専用 endpoint 方針を明記すべきである。

### logout / register の挙動決定

logout token 失効は現状 parity ではなく強化である。
register 後 auto-login するかも未決である。

どちらも `task-0-2` contract 表で決めるべきである。

### Cookie max-age / token exp / backend config

現状 access token 60分と Next cookie 30分の不整合があり、
Cookie 設定 source of truth が未整理である。

`task-1-1` に反映対象である。

### login request contract

既存 backend は `OAuth2PasswordRequestForm` である。
SPA 直呼びで JSON にするか form のままにするかを `task-0-2` に追加すべきである。

### rate limit / LoginSecurityService / security logging の維持

endpoint 新設時に漏れやすいので、`task-1-2` / `task-1-3` に明記すべきである。

### Docker / env / SPA fallback

`docker-compose.unified.yml` も対象に含めるべきである。

React Router の `/dashboard` 直アクセス用に `index.html` fallback も `task-3-2` に追加すべきである。

### integration test helper / SSO-SAML mock 方針

Cookie jar、CSRF header、IdP/JWKS/SAML の mock 方針は `task-1-4` に入れるべきである。

## 保留・設計判断として扱うべきもの

### SSO/SAML login POST の CSRF 除外

Antigravity の「除外すべき」は断定が強い。

OIDC `state/nonce`、PKCE、SAML RelayState / one-time ticket が CSRF 的な防御になるのは事実だが、
login CSRF や origin policy も絡む。

反映するなら「除外する」ではなく、`task-0-2` に
「SSO/SAML exchange endpoint の CSRF 要否を、state/nonce/RelayState/ticket/origin check と合わせて決定する」
と書くのが安全である。

### `task-2-1` の直列前提緩和

Vite scaffold は backend parity 前に並行可能である。

ただし削除ゲートは `task-3-1` にあり、実行効率の改善としては有用だが、
今の計画が誤りというほどではない。

### 存在しない `/profile` `/admin` `/settings` protected route

移植時整理として有用だが、現時点の計画へ強く入れるほどではない。

`task-2-3` の注意事項で十分である。

### `use-saml-login` の barrel export

移植時の細かい注意である。

必要なら `task-2-4` にチェック項目として追加する程度でよい。

### frontend test 基盤なし

現状認識として正しい。

ただし、今回の計画では backend integration + frontend build/typecheck + manual/E2E に寄せる方針なので、
すぐ追加必須ではない。

## 誤り、またはそのまま反映しない方がよいもの

### SSO/SAML login は CSRF 攻撃が成立しにくいので CSRF 除外とする結論

課題提起は正しいが、結論をそのまま採用するのは危険である。

設計判断事項に格下げして扱うべきである。

### `TokenWithRefresh` を既存 endpoint から単純に消す提案

ブラウザ向けには正しい方向だが、既存 API contract を破壊する。

Cookie 専用 endpoint 新設、Accept/header による切替、既存 endpoint 維持などの互換設計が先である。

### `docs/agent/app.md` の stale 記述

指摘自体はあり得るが、frontend SPA migration の直接範囲外である。

別の docs cleanup として保留でよい。

## 反映する場合の推奨順

1. `task-0-2` を強化する。
   API contract、既存 token JSON 互換、origin/CSRF/cookie 決定木、Users API 認可 parity、
   login/register/logout/refresh 方針を追加する。
2. `task-1-1` を強化する。
   Cookie 認証 dependency、CSRF 適用範囲、Cookie config source of truth を追加する。
3. `task-1-2` / `task-1-3` を強化する。
   refresh input、rate limit/security logging 維持、SSO/SAML CSRF 要否判断、
   logout/register の新規挙動明記を追加する。
4. `task-1-4` を強化する。
   Cookie/CSRF test helper と SSO/SAML mock 方針を追加する。
5. `task-3-2` を強化する。
   `docker-compose.unified.yml`、SPA fallback、env mapping 表を追加する。

## 結論

レビュー内容は「プランを否定するもの」ではなく、
`task-0-2` の contract 設計を厚くするべき、という方向の補強である。

コミット済みの計画を次コミットで改善する価値がある。
