# KOIKI-FW v0.7 Frontend SPA Migration Plan

## Purpose

This document defines the migration plan for replacing the current `frontend/`
Next.js implementation with a simpler React SPA.

The frontend is a reference implementation for:

- password login and registration
- SSO login
- SAML login
- access token / refresh token based authentication
- Todo CRUD

The objective is to reduce frontend framework complexity while preserving the
security properties currently provided by the Next.js route handlers.

## Decision Summary

The target architecture is:

- `frontend/` becomes a Vite + React + TypeScript SPA.
- React Router owns browser-side routing.
- FastAPI owns authentication cookies, CSRF validation, token refresh, logout,
  SSO token exchange, and SAML ticket exchange.
- The SPA does not store access tokens or refresh tokens in browser storage.
- The SPA calls backend APIs with `credentials: "include"`.
- State-changing requests send an `x-csrf-token` header.
- Next.js route handlers and middleware are removed after backend parity exists.

## Stakeholder Communication Summary

This migration is not only a decision to stop using Next.js in the current
reference frontend. The more important architectural decision is to establish an
authentication boundary that does not depend on any specific frontend
framework.

KOIKI-FW should lead authentication, token lifecycle, CSRF, SSO, and SAML
behavior from the backend. Frontend implementations should consume a clear
contract instead of reimplementing or proxying security-sensitive behavior.

This enables two outcomes at the same time:

1. the current reference frontend can become a simple React SPA
2. a future customer-specific Next.js frontend can be implemented more cleanly

If a customer later requires Next.js, Next.js should primarily provide UI,
routing, SSR/RSC, caching, and deployment integration. It should not become the
owner of token issuance, refresh token rotation, CSRF validation, SSO exchange,
or SAML ticket exchange.

## Problems In The Current Next.js Implementation

The current `frontend/` implementation uses Next.js as both a frontend
framework and a backend-for-frontend. That creates several problems.

### Security-Sensitive Behavior Is Split

Authentication behavior is split between FastAPI and Next.js route handlers.
The Next.js layer currently participates in:

- access token cookie issuance
- refresh token cookie issuance and rotation
- logout cookie clearing
- CSRF token generation and validation
- SSO authorization and login exchange proxying
- SAML authorization and login ticket exchange proxying
- authenticated Todo and User API proxying

This makes it harder to identify the true owner of authentication behavior.
It also increases the number of places that need security review when token or
SSO/SAML behavior changes.

### Frontend Framework Choice Affects Auth Design

Because auth cookies, refresh behavior, and CSRF behavior are implemented inside
Next.js route handlers, the reference frontend cannot be changed without also
moving security-sensitive logic.

That is a framework coupling problem. A reference application should be able to
switch between React SPA, Next.js, or another frontend without redefining the
backend authentication model.

### BFF Proxy Logic Duplicates Backend Concerns

The current Next.js route handlers mostly forward requests to FastAPI, but they
also add token extraction, response shaping, cookie handling, CSRF checks, and
some authorization checks. This creates a second API surface that must remain
consistent with the real backend API.

The duplication is especially risky around:

- error response shape
- token expiry and refresh failure behavior
- Cookie attributes
- CSRF failure handling
- SSO/SAML callback edge cases

### Reference Frontend Is More Complex Than Its Purpose

The frontend is intended to demonstrate login, SSO/SAML, token management, and
Todo behavior. The current Next.js implementation adds framework-specific
server behavior that obscures those reference flows.

For a starter/reference frontend, the useful demonstration is:

- how the browser initiates login
- how the browser calls authenticated APIs
- how CSRF is attached
- how callback pages complete SSO/SAML flows
- how Todo CRUD behaves after authentication

Those flows do not require Next.js-specific server infrastructure.

## Backend-Led Remediation

The remediation is to move the security-sensitive boundary into FastAPI and
make the frontend consume it through a stable contract.

FastAPI should own:

- password login and registration token issuance
- access token cookie issuance
- refresh token cookie issuance and rotation
- logout and token revocation
- auth cookie clearing
- CSRF token issuance and validation
- current-user resolution from Cookie credentials
- SSO authorization code exchange
- SAML login ticket exchange
- security logging and audit behavior

The frontend should own:

- UI state
- browser routing
- forms
- calling backend APIs with `credentials: "include"`
- sending the CSRF header on state-changing requests
- holding only transient public flow correlation data such as PKCE verifier,
  OIDC state/nonce, and SAML RelayState

This makes the backend the source of truth for security behavior while keeping
frontend implementations replaceable.

## React SPA Reference Implementation Rationale

The target reference implementation is a Vite + React + TypeScript SPA because
it demonstrates the frontend contract with the least framework-specific
machinery.

The SPA should be intentionally simple:

- no server-side frontend runtime
- no frontend-owned token storage
- no frontend-owned token refresh implementation beyond calling the backend
- no Next.js route handlers
- no auth proxy layer
- direct backend API calls through a small API client
- React Router for browser routes
- React Query for request state and cache invalidation

This reference implementation proves that KOIKI-FW's backend auth contract is
usable by a plain browser application. Once that contract is clear, a Next.js
frontend can consume the same contract in a thinner and more reviewable way.

## Future Next.js Compatibility

If a future customer requirement calls for Next.js, the recommended architecture
is not to restore the current BFF-heavy design.

Recommended Next.js role:

- page routing
- layouts and UI composition
- SSR / RSC where it adds product value
- metadata and cache behavior
- thin same-origin facade only when deployment requires it

Avoid in Next.js:

- issuing access or refresh tokens
- rotating refresh tokens
- validating SSO or SAML assertions
- owning CSRF validation as the source of truth
- duplicating backend authorization rules
- storing token values in browser-accessible storage

In this model, Next.js may call FastAPI from server components or route
handlers, but those calls should delegate to the backend auth contract rather
than implement auth behavior themselves.

## Why Not React Server Components

React Server Components are not a simple replacement for Next.js in this
repository. RSC requires server runtime integration, routing conventions, and
bundler support. Keeping RSC while removing Next.js would add a new server-side
frontend architecture and would not simplify this reference application.

The intended simplification is a browser-only React SPA paired with a FastAPI
backend that owns security-sensitive behavior.

## Current Frontend Responsibilities

The current `frontend/` implementation contains two separate concerns.

UI concerns:

- public landing page
- login and registration screens
- SSO and SAML callback screens
- authenticated dashboard
- Todo CRUD screens
- shared UI components, hooks, and types

Server/BFF concerns currently implemented with Next.js:

- authentication cookie issuance
- refresh token cookie rotation
- logout cookie clearing
- CSRF token generation and validation
- authenticated Todo and User API proxying
- SSO authorization proxying
- SSO login code exchange proxying
- SAML authorization proxying
- SAML login ticket exchange proxying
- protected route middleware

The migration should preserve the UI concerns in React and move the BFF concerns
to FastAPI.

## Target Security Model

### Token Storage

Access tokens and refresh tokens must not be stored in `localStorage`,
`sessionStorage`, IndexedDB, or non-httpOnly cookies.

FastAPI should issue:

- access token cookie
- refresh token cookie
- CSRF token cookie or CSRF response payload, depending on the final backend
  implementation

Authentication cookies should be configured with:

- `HttpOnly`
- `Secure` in production
- `SameSite=Lax` by default, unless cross-site deployment requires `None`
- `Path=/`
- no broad `Domain` attribute unless there is a documented deployment reason

Where production HTTPS and host constraints allow it, prefer `__Host-` cookie
prefixes for auth cookies.

### CSRF

Because browser cookies are sent automatically, cookie-authenticated state
changes require CSRF protection.

Backend requirements:

- validate CSRF on `POST`, `PUT`, `PATCH`, and `DELETE`
- do not require CSRF on safe `GET` requests
- reject missing or invalid CSRF tokens with a stable error code
- rotate or reissue CSRF tokens on login and refresh where appropriate
- avoid logging raw CSRF token values

Frontend requirements:

- call a CSRF bootstrap endpoint before state-changing operations when needed
- copy the current CSRF token into the configured header
- retry once only for known CSRF refresh failures if the backend supports it

### CORS And Deployment

If the SPA and API are served from different origins:

- backend CORS must allow only explicit frontend origins
- `Access-Control-Allow-Credentials` must be enabled
- wildcard origins must not be used with credentialed requests
- cookie `SameSite` and `Secure` settings must match the deployment model

If the SPA and API are served from the same origin:

- prefer same-origin API paths
- keep CORS disabled or minimal
- keep cookies host-only

### SSO And SAML

The frontend may store only transient public flow state:

- OIDC PKCE code verifier
- OIDC state / nonce correlation material
- SAML RelayState correlation material
- callback redirect targets

Backend must own:

- authorization code exchange
- SAML ticket exchange
- token pair creation
- cookie issuance
- SAML response validation
- RelayState / ticket expiration validation
- audit and security logging

## Scope

In scope:

- create a Vite React SPA replacement under `frontend/`
- migrate React pages and components away from Next.js APIs
- move current Next.js auth/proxy behavior into FastAPI
- update Docker and local development docs
- update frontend environment variable names
- update validation and test coverage for security-sensitive paths

Out of scope:

- redesigning the backend auth domain model
- replacing Keycloak or SAML provider behavior
- creating a production-grade design system
- adding new business features beyond the current reference flows
- converting the frontend to RSC through another meta-framework

## Backend Placement Rules

Follow repository boundary guidance:

- reusable auth, cookie, CSRF, token, middleware, and framework behavior belongs
  in `components/libkoiki/`
- current reference application SSO/SAML wiring belongs in
  `components/koiki_ref_app/`
- root `app/` remains a compatibility wrapper unless explicitly maintained

Todo remains a `libkoiki` starter/sample capability. Do not use the Todo API as
precedent for placing project-specific API behavior into `libkoiki`.

## Migration Strategy

The migration should be staged so that authentication behavior is not broken
midway.

1. Inventory and contract definition
2. Backend cookie-auth parity
3. Frontend SPA scaffold and API client replacement
4. Page and callback migration
5. Next.js removal
6. Docker, docs, and validation

Do not remove Next.js route handlers until backend endpoints provide equivalent
behavior and tests cover the security-sensitive paths.

## Task Directory

Detailed task instructions live under:

- `docs/dev/v0.7-frontend-spa-migration/`

Recommended execution order:

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

Minimum validation before considering the migration complete:

- backend tests prove login, refresh, logout, and CSRF behavior
- backend tests prove SSO and SAML exchange endpoints issue cookies correctly
- backend tests prove invalid CSRF is rejected for state-changing requests
- frontend typecheck passes
- frontend production build passes
- Docker frontend service starts and healthcheck passes
- manual or automated flow proves login -> Todo CRUD -> logout
- SSO and SAML happy paths are verified in the configured local environment

## Open Questions

- Should production deployment serve the SPA and API from the same origin?
- Should auth cookies use the current `koiki_*` names or move to `__Host-*`
  names with a compatibility window?
- Should CSRF be synchronizer-token based or signed double-submit cookie based?
- Which SSO/SAML callback URLs must remain backward compatible?
- Should the old Next.js implementation be removed in one branch or kept behind
  a short-lived fallback branch?

## Change Control

When this plan changes, update the task instructions under
`docs/dev/v0.7-frontend-spa-migration/` in the same change window if the change
affects execution order, scope, or completion criteria.

This English plan and the Japanese plan
`docs/dev/frontend-spa-migration-plan.ja.md` are synchronized documents. When
one is updated, review the other and update it in the same change window when
needed.
