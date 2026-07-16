# Frontend Contract Reference

Use this reference when root `frontend/` consumes or changes a backend API contract.

## Ownership

- `components/libkoiki/`: reusable API, session auth, Cookie/CSRF, shared auth and authorization behavior
- `components/koiki_ref_app/`: reference-app API, SSO, SAML, and app integration behavior
- `apps/`: downstream business backend API composition only
- root `frontend/`: reference browser consumer; never the owner of backend authorization or API placement

## Current SPA Pattern

- `shared/api/http-client.ts`: credentials, CSRF initialization/retry, JSON parsing, `ApiError`
- `features/<feature>/api.ts`: typed endpoint calls through the shared transport
- `features/<feature>/queries.ts`: TanStack Query key, query, mutation, and cache behavior
- `routes/` and `components/`: routing, forms, interaction, and presentation

Use `requestJson<T>()` for new feature API functions. Handle 204 responses, normalized errors, and feature-specific cache updates deliberately.

## Browser Auth Contract

- use `/api/v1/auth/session/*` with `credentials: "include"`
- backend owns access / refresh Cookie issuance, refresh, logout, and CSRF validation
- do not store access or refresh tokens in localStorage or sessionStorage
- use the shared transport for Cookie-authenticated unsafe requests
- preserve the distinction from token-returning Bearer-client endpoints
- SSO / SAML authorization and session exchange are security-sensitive browser flows; pair this skill with `koiki-auth-security` when they change

## Contract Change Checklist

For an API consumed by the frontend, check:

1. request and response type changes
2. status code, error payload, 204 response, or 409 conflict behavior
3. backend authorization and frontend UX behavior separately
4. Cookie/CSRF and session/Bearer compatibility
5. Vite public configuration versus backend-owned settings
6. feature API, Query invalidation, form handling, and focused frontend tests

## Source of Truth

- `docs/frontend-spa-implementation-guide.ja.md`
- `docs/authentication-api-guide.md`
- `docs/dev/agent-skills-framework-app-alignment-tasks/task-0-2-contract-impact-map.ja.md`
