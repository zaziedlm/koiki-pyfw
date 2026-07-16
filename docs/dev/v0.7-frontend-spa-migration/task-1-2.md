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

実施済み。

- `libkoiki` に `/api/v1/auth/session/*` endpoint を追加した。
  - `GET /session/csrf`
  - `POST /session/login`
  - `POST /session/register`
  - `POST /session/refresh`
  - `POST /session/logout`
  - `GET /session/me`
- 既存 `/api/v1/auth/login` の token-returning contract は維持し、password 認証・LoginSecurityService・security logging・token pair 発行処理だけを session login と共有した。
- session login / refresh は response body に access token / refresh token を返さず、Cookie でのみ token を更新する。
- session register は auth Cookie を発行せず、CSRF Cookie の更新だけを行う。
- session refresh は refresh Cookie から token を読み、失敗時は auth Cookie / CSRF Cookie を clear する。
- session logout は現在の refresh Cookie に対応する refresh token を失効し、Cookie を clear する。
- session `me` は Task 1-1 の Cookie fallback により `ActiveUserDep` 経由で current user を返す。

検証:

```text
DEBUG=False uv run pytest \
  components/libkoiki/tests/unit/libkoiki/api/test_auth_session.py \
  components/libkoiki/tests/unit/libkoiki/api/test_auth_logging.py \
  components/libkoiki/tests/unit/core/test_auth_cookie_csrf.py \
  components/libkoiki/tests/unit/libkoiki/test_token_logging.py \
  tests/unit/test_pyjwt_migration.py
```

結果:

```text
56 passed, 7 warnings
```

補足:

- request/DI/DB を含む full-stack の session flow 検証は Task 1-4 の integration tests で扱う。
- Users API authorization parity は Task 1-4 の integration scope で、BFF 削除後の権限低下がないことを確認する。
