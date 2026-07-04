# Task 1-2: password auth Cookie endpoints

## 目的

password login、registration、refresh、logout、me を SPA 向け Cookie 認証 contract に対応させる。

## 事前条件

- Task 1-1 が完了している

## 対象

- `POST /api/v1/auth/session/login`
- `POST /api/v1/auth/session/register`
- `POST /api/v1/auth/session/refresh`
- `POST /api/v1/auth/session/logout`
- `GET /api/v1/auth/session/me`
- `GET /api/v1/auth/session/csrf`
- existing token-returning `/api/v1/auth/*` endpoint compatibility

## 実施手順

1. 既存 token-returning endpoint を壊さず、Cookie session endpoint を新設する
2. session login 成功時に access / refresh Cookie を発行する
3. session login response body から token value を返さない
4. 既存 rate limit、LoginSecurityService、security logging、security metrics を維持する
5. session register は現行どおり register-then-login とし、auth Cookie を発行しない
6. session refresh は refresh token を request body ではなく Cookie から読む
7. session refresh 成功時に token rotation と Cookie 更新を行う
8. session refresh response body から token value を返さない
9. refresh 失敗時に auth Cookie を clear する
10. session logout 時に現在の refresh token 失効と Cookie clear を行う
    - この挙動は現状 parity ではなく強化であるため、失効範囲を contract に合わせる
11. session `me` が Cookie 認証で current user を返せるようにする
12. CSRF bootstrap endpoint を追加する
13. Users API authorization parity に従い、backend 側 endpoint / dependency に反映する

## 検証

- session login 成功時に auth Cookie が設定される
- session register 成功時に auth Cookie が設定されない
- session refresh 成功時に Cookie が更新される
- refresh 失敗時に Cookie が clear される
- session logout 後に `me` が 401 になる
- session endpoint response body に token value を返さないことがテストで確認できる
- 既存 Bearer client 向け token-returning contract の互換性がテストで確認できる
- login security / rate limit / security logging が維持されている
- Users API の権限が BFF 削除で緩んでいない

## 完了条件

- password auth flow が Next.js route handler なしで成立する
- refresh / logout / register の新規挙動と parity 挙動が区別されている

## 実施結果

未実施。
