# Task 1-3: SSO / SAML Cookie endpoints

## 目的

SSO と SAML の login exchange 後に FastAPI が直接 auth Cookie を発行できるようにする。

## 事前条件

- Task 1-1 が完了している
- Task 1-1 の Cookie 発行 helper が利用可能である

## 対象

- `GET /api/v1/auth/sso/authorization`
- `POST /api/v1/auth/session/sso/login`
- `GET /api/v1/auth/saml/authorization`
- `POST /api/v1/auth/session/saml/login`
- existing token-returning `/api/v1/auth/sso/login` and `/api/v1/auth/saml/login` compatibility

## 実施手順

1. SSO authorization init の response contract を SPA 向けに確認する
2. 既存 token-returning SSO / SAML login endpoint を壊さず、Cookie session exchange endpoint を新設する
3. session SSO login exchange 成功時に access / refresh Cookie を発行する
4. SAML authorization init の response contract を SPA 向けに確認する
5. session SAML login ticket exchange 成功時に access / refresh Cookie を発行する
6. session SSO / SAML login exchange response body から token value を返さない
7. session SSO / SAML exchange endpoint に CSRF を要求する
8. Origin / CSRF / state / nonce / RelayState / ticket expiry の検証責務を確認する
9. 既存 security logging / security metrics を維持する
10. backend security logging が raw token や raw assertion を出さないことを確認する

## 検証

- session SSO exchange 成功時に Cookie が発行される
- session SAML exchange 成功時に Cookie が発行される
- invalid state / RelayState / ticket は拒否される
- frontend は token value を受け取らなくても dashboard へ遷移できる
- CSRF と代替防御の組み合わせが Task 0-2 の contract と一致している
- session response body に token value を返さないことがテストで確認できる
- 既存 token-returning SSO / SAML endpoint の互換性がテストで確認できる
- security logging / metrics が既存 flow と同等に維持されている

## 完了条件

- SSO / SAML flow が Next.js route handler なしで成立する

## 実施結果

実施済み。

- `koiki_ref_app` の既存 SSO / SAML token-returning endpoint は維持した。
  - `POST /api/v1/auth/sso/login`
  - `POST /api/v1/auth/saml/login`
- SPA 向け Cookie session exchange endpoint を追加した。
  - `POST /api/v1/auth/session/sso/login`
  - `POST /api/v1/auth/session/saml/login`
- SSO / SAML の exchange、state / nonce / RelayState / ticket 検証、security logging、security metrics、内部 token pair 発行処理は既存 flow と共有した。
- session SSO / SAML login は CSRF cookie/header pair を必須にし、成功時に access / refresh / CSRF Cookie を発行する。
- session SSO / SAML login response body は `message`, `user`, `location` のみとし、access token / refresh token value を返さない。
- SSO authorization init と SAML authorization init は既存 response contract のまま SPA から利用可能と判断した。

検証:

```text
DEBUG=False uv run pytest \
  components/koiki_ref_app/tests/unit/app/test_session_sso_saml_auth.py \
  components/koiki_ref_app/tests/unit/app/test_sso_auth_logging.py \
  components/koiki_ref_app/tests/unit/app/test_saml_auth_logging.py \
  components/libkoiki/tests/unit/libkoiki/api/test_auth_session.py \
  components/libkoiki/tests/unit/core/test_auth_cookie_csrf.py
```

結果:

```text
31 passed, 4 warnings
```

補足:

- invalid state / RelayState / ticket の拒否は既存 service / token endpoint flow と共有しているため、個別の service-level tests と Task 1-4 の integration tests で full-stack に確認する。
- frontend の dashboard 遷移確認は Task 2 系の SPA client 移行後に実施する。
