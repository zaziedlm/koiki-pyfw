# Frontend Enterprise Readiness Audit (Next.js 15)

- Target: `frontend/` (Next.js 15, React 19, App Router)
- Backend: FastAPI (BFF-style proxy via Next Route Handlers)
- Date: 2025-09-04

## Executive Summary

Overall, the prototype demonstrates solid foundations for an enterprise-grade frontend: secure cookie-based authentication, CSRF protection via double-submit token pattern, Docker hardening (non-root, custom CA trust), and reasonable separation between UI and BFF endpoints. The implementation is close to production-ready for a pilot, but several hardening and operational gaps remain: missing defense-in-depth headers (CSP, HSTS, COOP/COEP/CORP, Referrer-Policy, Permissions-Policy), lack of rate limiting on BFF endpoints, no observability tooling (Sentry/Otel), and no CI coverage for the frontend. A couple of correctness issues should also be fixed before wider use (noted below).

Risk level: Medium (addressable via the prioritized actions).

## Highlights (Strengths)

- Cookie-based auth with httpOnly; no tokens in web storage.
  - `frontend/src/lib/cookie-utils.ts:1` and usage in auth routes.
- CSRF protection using double-submit cookie + header; regenerated on auth flows.
  - `frontend/src/lib/csrf-utils.ts:1`, `frontend/src/app/api/auth/csrf/route.ts:1`.
- BFF route handlers proxy to backend and isolate tokens from the browser.
  - `frontend/src/app/api/**` proxy patterns.
- Sensible cookie attributes (httpOnly, SameSite=Lax, Secure in production).
  - `frontend/src/lib/cookie-utils.ts:18`.
- Docker: multi-stage, non-root user, custom CA, healthcheck.
  - `frontend/Dockerfile:1`.
- App Router used with clear feature separation; TanStack Query for data.

## Gaps and Risks (Summary)

- Missing core security headers (CSP, Referrer-Policy, HSTS, COOP/COEP/CORP, Permissions-Policy); only `X-Frame-Options` and `X-Content-Type-Options` are present.
  - `frontend/next.config.ts:24`.
- No abuse controls on BFF routes (rate limiting, bot mitigation, simple IP throttling).
- Observability lacking: no Sentry, no OpenTelemetry traces/metrics, limited structured logging.
- No frontend CI (type check, lint, build) and no tests (unit or e2e) in workflows.
  - `.github/workflows/ci.yml` is backend-only.
- Middleware runtime export appears invalid for Next middleware and should be removed.
  - `frontend/src/middleware.ts:5`.
- Minor correctness: duplicate variable declaration in `cookie-api-client.ts` (will fail type-check/build when touched).
  - `frontend/src/lib/cookie-api-client.ts:218-224` and again at line `:278` for users.
- A few logs in route handlers are unguarded for production.
  - `frontend/src/app/api/auth/login/route.ts:57`.

---

## Detailed Findings

### 1) Authentication & Session Management

- Cookie-based tokens are set as httpOnly with SameSite=Lax, Secure in production.
  - `frontend/src/lib/cookie-utils.ts:18` and related setters.
- CSRF protection uses a double-submit cookie (`koiki_csrf_token`) and a custom header `x-csrf-token` validated server-side. New CSRF issued after login/register/refresh.
  - Generation/validation: `frontend/src/lib/csrf-utils.ts:1`.
  - Token issuance endpoint: `frontend/src/app/api/auth/csrf/route.ts:1`.
  - Enforced on state-changing endpoints (e.g., todos/users write operations).
    - e.g., `frontend/src/app/api/todos/route.ts:1` (POST), `frontend/src/app/api/users/[id]/route.ts` (PUT/DELETE), etc.
- Recommendations
  - Prefix cookies in production with `__Host-` to enforce host-only, secure semantics (requires path=/, no domain attribute).
  - Consider opaque session identifiers at the BFF with server-side session validation or short-lived access tokens + strict rotation for refresh tokens.
  - Add detection and invalidation of stolen/rotated tokens (e.g., refresh token rotation and reuse detection) on the backend; expose minimal signals to the frontend for UX.

### 2) Security Headers & Platform Hardening

- Current headers: only `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
  - `frontend/next.config.ts:24`.
- Recommended additions (gate via env `NEXT_PUBLIC_ENABLE_SECURITY_HEADERS`):
  - Content-Security-Policy (CSP) with nonce or hashes, tailored for Next.js (scripts, styles, fonts, images) and your domains. Provide Report-Only in staging.
  - Referrer-Policy: `strict-origin-when-cross-origin`.
  - Strict-Transport-Security (HSTS): only when served behind TLS, with preload as appropriate.
  - Permissions-Policy: restrict camera, microphone, geolocation, etc.
  - Cross-Origin-* policies: COOP `same-origin`, CORP `same-origin`, and COEP if you need advanced isolation.
  - Cache-Control for sensitive API responses: `no-store` or `private, no-store`.

Example (to adapt in `next.config.ts`):

```ts
// next.config.ts (excerpt)
async headers() {
  const enabled = process.env.NEXT_PUBLIC_ENABLE_SECURITY_HEADERS === 'true';
  if (!enabled) return [];
  return [
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        // Only under HTTPS/edge: enable HSTS
        // { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
        { key: 'Cross-Origin-Resource-Policy', value: 'same-origin' },
        // Optional: COEP if required by your isolation strategy
        // { key: 'Cross-Origin-Embedder-Policy', value: 'require-corp' },
      ],
    },
  ];
}
```

For CSP, prefer strict `script-src 'self' 'nonce-<generated>'` with nonces attached in layout for inline scripts when/if needed; avoid `unsafe-inline` for production.

### 3) BFF Route Handlers (APIs)

- BFF endpoints correctly forward auth via server-side cookies and avoid exposing tokens to the browser.
  - e.g., `frontend/src/app/api/auth/*`, `frontend/src/app/api/todos/*`, `frontend/src/app/api/users/*`.
- Some reads deliberately mark `cache: 'no-store'` (good), but this is not consistent across all fetches.
  - e.g., `frontend/src/app/api/users/me/route.ts:18` sets no-store; many others do not.
- Recommendations
  - For all auth-dependent BFF responses, ensure `no-store` and avoid unintended caching. Optionally add `export const dynamic = 'force-dynamic'` on routes that must never be cached.
  - Normalize backend error handling and sanitize backend error messages before exposing to clients.
  - Ensure all write operations validate CSRF (already done) and consider idempotency keys for critical mutations.

### 4) Middleware

- `export const runtime = 'nodejs'` is not supported for middleware (middleware always runs in Edge runtime). Remove the export to avoid confusion or build-time issues.
  - `frontend/src/middleware.ts:5`.
- JWT “format” validation is minimal by design; actual validity is enforced server-side, which is appropriate. Keep middleware lightweight and rely on BFF checks.

### 5) Observability & Auditability

- Currently no centralized error reporting or tracing.
- Recommendations
  - Add Sentry (browser + Next Route Handlers) to capture exceptions, with PII scrubbing.
  - Consider OpenTelemetry tracing (e.g., simple SDK with OTLP to collector) to trace frontend BFF -> backend requests.
  - Use a structured logger for server-side logs; guard console logs in production or send to centralized logging.

### 6) Abuse Prevention

- No rate limiting on BFF endpoints or auth routes. Add simple IP-based throttling for login/register/refresh and CSRF issuance.
  - Start with in-memory/LRU for dev; production with Redis/Upstash based limiter.
- Consider bot protection on public forms (e.g., turnstile/reCAPTCHA) if exposed to internet.

### 7) CI/CD & Testing

- No frontend CI job present; backend-only pipeline at `.github/workflows/ci.yml`.
- Recommendations
  - Add Node LTS job: `npm ci`, `npm run lint`, `tsc --noEmit`, `npm run build`.
  - Add unit tests (Vitest) for critical utils and hooks.
  - Add Playwright e2e smoke: login, dashboard access, CRUD on todos.
  - Gate builds on type/lint/test success.

### 8) Accessibility & i18n

- ESLint config includes Next defaults (which bring a11y rules), but no explicit a11y tests or checks.
  - `frontend/eslint.config.mjs:1`.
- Consider automated a11y checks (axe via Playwright) and keyboard/screen reader validation in CI.
- If multilingual requirements exist, introduce i18n (e.g., `next-intl` or `next-i18next`) with locale routing.

### 9) Performance & UX

- Use TanStack Query with sane defaults; SSR is not used for protected pages (reasonable).
- Consider:
  - Setting `staleTime`/`gcTime` per-query for hot data.
  - Deferring large components and using `React.lazy` or route-level streaming where useful.
  - Applying `Cache-Control` headers for static assets via Next config or CDN.

### 10) Docker & Supply Chain

- Good: multi-stage build, non-root, custom CA trust, healthchecks.
  - `frontend/Dockerfile`.
- Additional recommendations:
  - Pin base images by digest for reproducibility.
  - Add `--omit=dev` (already used) and consider pruning optional files in final image.
  - Dependabot or Renovate for npm dependency updates.

---

## Immediate Fixes (Blocking/Important)

1) Remove invalid middleware runtime export
- File: `frontend/src/middleware.ts:5`
- Action: Remove `export const runtime = 'nodejs';` (middleware always runs on Edge runtime in Next 15).

2) Fix duplicate variable declaration causing build/type error
- File: `frontend/src/lib/cookie-api-client.ts:218-224`
- Issue: Variable `queryString` is declared twice for `cookieTodoApi.getAll` in earlier history (ensure only one declaration remains). Also verify the similar pattern for users list at `:277-280`.

3) Guard production logs in route handlers
- File: `frontend/src/app/api/auth/login/route.ts:57`
- Action: Wrap in `if (process.env.NODE_ENV === 'development') { ... }` or standardize a server logger.

4) Implement comprehensive security headers (CSP, Referrer-Policy, HSTS, COOP/CORP)
- File: `frontend/next.config.ts`
- Action: Add recommended headers gated by env, as shown above.

5) Add rate limiting to auth-related endpoints and CSRF issuance
- Files: `frontend/src/app/api/auth/*`, `frontend/src/app/api/auth/csrf/route.ts`
- Action: Introduce IP-based throttling (e.g., Redis/Upstash), with safe fallbacks in development.

---

## Recommended Next Steps (Prioritized)

1) Add security headers and CSP (Report-Only in staging; strict in prod).
2) Fix middleware runtime export; fix duplicate variable declaration.
3) Add frontend CI: lint, type-check, build; add Playwright smoke tests and Vitest unit tests.
4) Introduce Sentry/Otel for error and trace capture.
5) Add rate limiting to public/auth BFF endpoints; consider bot protection for login/register.
6) Harden cookies (`__Host-` prefix) and confirm refresh-token rotation strategy in backend.
7) Normalize `no-store` on sensitive BFF endpoints and avoid caching for user-bound data.
8) Establish dependency update policy (Dependabot/Renovate) and periodic `npm audit` gates.
9) Add i18n and a11y test coverage if required by product scope.
10) Document operational runbooks (token incident handling, CSRF rotation, header regression tests).

---

## File References (Not Exhaustive)

- Middleware: `frontend/src/middleware.ts:1`
- Security headers: `frontend/next.config.ts:1`
- Cookie utils: `frontend/src/lib/cookie-utils.ts:1`
- CSRF utils: `frontend/src/lib/csrf-utils.ts:1`
- CSRF endpoint: `frontend/src/app/api/auth/csrf/route.ts:1`
- Auth routes: `frontend/src/app/api/auth/login/route.ts:1`, `.../refresh/route.ts:1`, `.../logout/route.ts:1`, `.../register/route.ts:1`, `.../me/route.ts:1`
- Todos BFF: `frontend/src/app/api/todos/route.ts:1`, `.../todos/[id]/route.ts:1`
- Users BFF: `frontend/src/app/api/users/route.ts:1`, `.../users/[id]/route.ts:1`, `.../users/me/route.ts:1`
- Client API client: `frontend/src/lib/cookie-api-client.ts:1`
- Config/env samples: `frontend/.env.local.example:1`, `frontend/.env.docker:1`
- Docker: `frontend/Dockerfile:1`
- CI (backend only): `.github/workflows/ci.yml:1`

---

## Closing Note

The prototype is well-structured and applies modern Next.js patterns with robust auth fundamentals. Addressing the listed hardening items—especially headers/CSP, rate limiting, observability, and CI coverage—will move it to an enterprise-ready posture. I can raise a follow-up PR to implement the quick fixes (middleware export, duplicate var) and a baseline security-headers configuration if desired.

