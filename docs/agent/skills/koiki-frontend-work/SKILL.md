---
name: koiki-frontend-work
description: Use when implementing or reviewing root frontend Vite + React SPA work, including routes, UI components, feature API clients, TanStack Query, forms, browser auth/CSRF integration, frontend configuration, and frontend tests. Use with the owning backend skill when an API contract changes. Do not use this skill to implement backend APIs or place frontend code under apps/.
---

# KOIKI Frontend Work

Use this skill for the root `frontend/` reference SPA. Vite + React is the current recommended implementation style; the API, authorization, Cookie/CSRF, error, configuration, and test contracts remain relevant to another frontend technology.

## Scope

- routes, layouts, UI components, forms, and client-only state under root `frontend/`
- feature API functions, TanStack Query keys / queries / mutations, transport error handling, and frontend tests
- browser use of backend-owned Cookie session, CSRF, SSO, and SAML contracts
- Vite public configuration, static SPA delivery, and frontend CI checks

Do not implement backend API ownership, authorization, Cookie issuance, refresh, logout, or CSRF validation here. Do not create frontend code under `apps/`.

## Workflow

1. Confirm the task belongs to root `frontend/`. If API ownership is unclear, start with `koiki-project-overview`.
2. For an API contract change, identify the owning backend layer and use its backend Skill as well. Check schema, status/error behavior, authorization, Cookie/CSRF, public config, and consumer tests.
3. Reuse the existing frontend boundaries:
   - `shared/api/` owns credentials, CSRF, JSON parsing, and `ApiError`
   - `features/<feature>/api.ts` owns endpoint calls
   - `features/<feature>/queries.ts` owns query keys, Query hooks, and cache updates
   - route and component code owns UI events, forms, and presentation
4. Use backend session endpoints with `credentials: "include"`. Do not store access or refresh tokens in browser storage.
5. For Cookie-authenticated unsafe requests, use the shared transport so CSRF initialization and one retry for `CSRF_TOKEN_INVALID` remain consistent.
6. Add the smallest frontend validation that proves the changed risk. Use backend integration coverage for backend enforcement; do not replace it with a UI test.

## Guardrails

- Do not call `fetch` directly from UI components when the shared transport and feature API pattern applies.
- Do not use a route guard or hidden UI control as authorization enforcement.
- Do not duplicate backend Cookie, CORS, CSRF, or security-header settings in frontend configuration.
- Do not treat a token-returning Bearer endpoint as the browser session endpoint without an explicit compatibility decision.
- Do not put project-specific frontend code under `apps/`.

## Validate

- API transport / error / CSRF behavior: focused Vitest + MSW coverage
- Query or mutation changes: feature query / cache invalidation coverage
- form or route behavior: component coverage when there is regression risk
- backend contract changes: matching backend unit or integration coverage through the owning backend Skill
- frontend changes: `npm test`, `npm run check-types`, `npm run lint`, `npm run build` as applicable

## Read Next

- `docs/frontend-spa-implementation-guide.ja.md`
- `references/frontend-contract.md`
- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/auth-security.md`
- `docs/agent/testing.md`
- `docs/agent/skills/koiki-project-overview/SKILL.md`
- `docs/agent/skills/koiki-auth-security/SKILL.md`
- `docs/agent/skills/koiki-testing/SKILL.md`
