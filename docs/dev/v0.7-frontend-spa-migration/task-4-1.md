# Task 4-1: final validation / release notes

## 目的

Frontend SPA migration の完了判定を行い、残課題とリリース時の注意点を文書化する。

## 事前条件

- Task 3-2 が完了している

## 実施手順

1. backend auth integration tests を実行する
2. frontend typecheck を実行する
3. frontend production build を実行する
4. Docker または local dev で login -> Todo CRUD -> logout を確認する
5. SSO happy path を確認する
6. SAML happy path を確認する
7. docs と README の古い Next.js 記述を検索する
8. release notes に breaking changes と migration notes をまとめる

## 検証

- auth Cookie が JS から読めない
- Cookie 認証された state-changing request は CSRF なしで失敗する
- Bearer-token client は CSRF なしでも contract どおり動作する
- token refresh 後も authenticated state が維持される
- logout 後に protected route へ戻れない

## 完了条件

- 移行結果、検証結果、残課題が文書化されている
- frontend は Next.js なしで起動・build・運用できる

## 実施結果

実施済み。

## 検証結果

Backend auth integration:

- `DEBUG=False RUN_DB_INTEGRATION=1 DATABASE_URL=postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db uv run pytest components/koiki_ref_app/tests/integration/app/api/test_auth_session_api.py`
- Result: 10 passed.
- Covered:
  - session password login sets auth Cookie and does not expose token values in response body
  - Cookie auth resolves current user
  - Cookie-authenticated unsafe request requires valid CSRF
  - Bearer-authenticated unsafe request does not require CSRF
  - session refresh rotates Cookie and hides token values
  - logout clears Cookies and `me` returns 401 after logout
  - Users API permission parity with Cookie auth
  - existing token-returning login / refresh contract still returns token values

Frontend:

- `npm run check-types`
- Result: passed.
- `npm run build`
- Result: passed.
- Note: Vite emitted a large chunk warning for `assets/index-*.js`; this is not a build failure. Code splitting can be treated as a later performance task.

Docker / runtime:

- `docker compose -f docker-compose.unified.yml --profile prod ps`
- Result: all expected services are healthy:
  - `app-prod` -> `0.0.0.0:8000->8000/tcp`
  - `frontend-prod` -> `0.0.0.0:3000->8080/tcp`
  - `db`
  - `keycloak`
- User browser validation:
  - login succeeded
  - dashboard opened
  - Todo screen opened
  - new Todo task creation succeeded from UI
- Backend log validation:
  - `POST /api/v1/auth/session/login` returned 200
  - `GET /api/v1/auth/session/me` returned 200 after login
  - authenticated actor used `auth_method: cookie`
  - `POST /api/v1/todos` returned 201
  - Todo insert and DB commit were observed
  - no unexpected backend 500 / traceback was observed in the checked flow

Next.js removal checks:

- `rg 'next/|NextRequest|NextResponse|next-themes|eslint-config-next|next/core-web-vitals|next/typescript' frontend/src frontend/package.json frontend/package-lock.json frontend/tsconfig.json frontend/eslint.config.mjs`
- Result: no matches.
- `rg '"next"|@next/' frontend/package.json frontend/package-lock.json`
- Result: no matches.

Docs / README search:

- Active frontend README and implementation docs have been updated for Vite SPA.
- Historical or pre-migration documents still contain Next.js / BFF descriptions:
  - `docs/authentication-api-guide.md`
  - `docs/frontend-application-development-guide.md`
  - `docs/FRONTEND_ENTERPRISE_AUDIT.md`
  - `docs/FRONTEND_ENTERPRISE_AUDIT_ja.md`
  - `docs/dev/env-files.md`
  - `docs/dev/frontend-next15-guide.md`
  - old v0.7 release check result documents
- These are not active frontend runtime dependencies, but should be revised or explicitly archived before publishing this line as the current frontend guidance.

## 残課題

- SSO happy path and SAML happy path with a real IdP were not re-run during this final pass. Callback implementation and backend session exchange coverage are present, but real-provider end-to-end confirmation remains a release-gate item.
- Local `unified-prod` logs still show the development/test JWT secret length warning. Actual production / AWS deployment must use a strong secret of at least 32 bytes for HS256.
- Local `unified-prod` still reports environment metadata as development in logs. Before production release, production environment values should be reviewed and set explicitly.
- Vite production build emits a large chunk warning. This is acceptable for this migration, but later code splitting may be useful.
- Historical Next.js-oriented docs should be updated or archived so that new readers do not treat them as current guidance.

## Release notes draft

Breaking changes:

- The reference frontend has moved from Next.js BFF to Vite React SPA.
- Frontend no longer owns auth Cookie issuance, token refresh, CSRF validation, SSO exchange, or SAML ticket exchange.
- Browser auth flows use backend session endpoints and backend-managed httpOnly Cookies.
- SPA API calls use `credentials: "include"` and send `x-csrf-token` for Cookie-authenticated state-changing requests.
- `NEXT_PUBLIC_*` frontend runtime configuration has been replaced by `VITE_*` build-time configuration where frontend visibility is required.
- Production frontend container serves static `dist/` through unprivileged nginx on container port `8080`; compose publishes it as host port `3000`.

Compatibility notes:

- Existing token-returning login / refresh endpoints remain covered for non-browser Bearer-token clients.
- Cookie session endpoints intentionally do not return access or refresh token values in response bodies.
- Bearer-token clients are not required to send CSRF tokens under the current contract.
- Public registration remains separate from admin user creation; Users API permission parity was covered by integration tests.

Migration notes:

- Build frontend configuration with `VITE_API_BASE_URL`, `VITE_SSO_REDIRECT_URI`, and `VITE_SAML_REDIRECT_URI` appropriate for the deployment origin.
- For same-origin production deployment, prefer a reverse proxy or ALB routing model where the SPA and API share the browser origin.
- For cross-origin deployment, ensure backend CORS allowed origins, Cookie `SameSite` / `Secure`, and CSRF transport settings match the deployment topology.
- Configure production JWT / Cookie / CSRF secrets and security attributes before release.
