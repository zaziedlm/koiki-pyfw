# Task 1-4: backend auth integration tests

## 目的

Cookie 認証、CSRF、refresh、SSO、SAML の backend behavior を integration test で固定する。

## 事前条件

- Task 1-1 から Task 1-3 が完了している

## 実施手順

1. session password login の Cookie 発行を検証する
2. CSRF bootstrap と Cookie 認証された state-changing request の成功を検証する
3. Cookie 認証された request における invalid CSRF の拒否を検証する
4. Bearer-token client に CSRF を要求しないことを検証する
5. Cookie 認証で current user を解決できることを検証する
6. refresh token rotation と Cookie 更新を検証する
7. refresh 失敗時の Cookie clear を検証する
8. logout 後の `me` 401 を検証する
9. Users API authorization parity を検証する
10. 既存 token-returning login / refresh / SSO / SAML endpoint の互換性を検証する
11. session SSO / SAML exchange の Cookie 発行を検証する
12. SSO / SAML invalid state 系の拒否を検証する
13. session endpoint response body に token value が含まれないことを検証する
14. Cookie jar と CSRF header を扱う test helper を用意する
15. SSO / SAML integration test の mock 方針を決める
    - IdP token endpoint
    - JWKS / ID token verification
    - SAML response / login ticket
    - service boundary stub の利用可否

## 検証

- auth security-sensitive paths に integration coverage がある
- DEBUG 環境変数は repository guidance に従って boolean value を設定して実行する
- Cookie / CSRF test helper により、重複した test setup が増えすぎていない
- SSO / SAML の外部依存 mock 方針が文書化されている
- 既存 Bearer / token-returning contract と新しい Cookie session contract が別々に検証されている

## 完了条件

- Next.js route handler 削除前の backend parity がテストで確認できている
- parity ではなく強化した挙動は、期待仕様として明示された上でテストされている

## 実施結果

実施済み。

- Cookie / CSRF helper を integration tests に追加した。
- password session login の Cookie 発行と token body 非露出を検証した。
- Cookie 認証で `GET /auth/session/me` が current user を解決できることを検証した。
- Cookie 認証された `PUT /users/me` は CSRF を要求し、invalid CSRF を拒否することを検証した。
- Bearer token 認証の `PUT /users/me` では CSRF を要求しないことを検証した。
- session refresh の token rotation / Cookie 更新 / token body 非露出を検証した。
- refresh 失敗時に auth Cookie clear header が返ることを検証した。
- session logout 後に `GET /auth/session/me` が 401 になることを検証した。
- Users API の権限 parity として、一般ユーザー Cookie 認証で `/users` が 403 になることを検証した。
- 既存 token-returning login / refresh endpoint が token body を返し続けることを検証した。
- session SSO / SAML exchange は service boundary stub を使い、router 経由で Cookie 発行と token body 非露出を検証した。

実装補足:

- Users API の unsafe endpoint に `CookieCSRFDep` を追加した。
  - Cookie 認証された unsafe request のみ CSRF を検証する。
  - Bearer token client には CSRF を要求しない。
- session response の user payload は ORM lazy relationship に触れない明示 dict にした。

SSO / SAML integration test の mock 方針:

- IdP token endpoint、JWKS / ID token verification、SAML response verification は外部依存としてこの task では直接叩かない。
- state / nonce / RelayState / ticket verification は既存 service / token endpoint flow と共有し、service-level tests と既存 logging tests に委ねる。
- session endpoint 固有の責務である CSRF、Cookie 発行、token body 非露出は router 経由で検証する。

検証:

```text
docker compose up -d --force-recreate db
docker compose ps db
DEBUG=False RUN_DB_INTEGRATION=1 DATABASE_URL=postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db \
  uv run pytest components/koiki_ref_app/tests/integration/app/api/test_auth_session_api.py
```

結果:

```text
10 passed, 12 warnings
```

関連 unit:

```text
DEBUG=False uv run pytest \
  components/libkoiki/tests/unit/libkoiki/api/test_auth_session.py \
  components/koiki_ref_app/tests/unit/app/test_session_sso_saml_auth.py
```

結果:

```text
11 passed
```
