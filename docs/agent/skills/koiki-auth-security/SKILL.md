---
name: koiki-auth-security
description: Use when working on authentication, authorization, RBAC, token flows, security monitoring, SSO, or SAML-related behavior across components/libkoiki/ and components/koiki_ref_app/.
---

# KOIKI Auth and Security

Use this skill for security-sensitive work. Favor correctness, consistency, and explicit validation.

## Scope

This skill applies to:

- JWT and token handling
- RBAC and permission checks
- login and password flows
- security logging and monitoring
- SSO and SAML integration

## Future Role Alignment

This skill remains cross-cutting across future maintainer and template skill families. Auth and security work often spans `components/libkoiki`, `components/koiki_ref_app`, and frontend/browser flows, so it should not be split prematurely.

## Workflow

1. identify whether the change is framework auth, app-specific SSO/SAML, or both
2. trace the full request flow before editing
3. preserve existing security boundaries and failure behavior
4. update validation, logging, and test coverage together
5. review for unintended privilege, token, redirect, or session regressions

## Guardrails

- do not weaken validation, rate limiting, or audit behavior without explicit reason
- do not change auth flows in only one layer if the behavior spans framework and app code
- do not assume frontend-only controls are sufficient for authorization

## Validate

- security-relevant unit tests
- affected integration or API tests
- SSO/SAML edge cases when applicable

## Read Next

- `docs/agent/auth-security.md`
- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/testing.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`
- `references/auth-security-reference.md`
- `docs/agent/skills/future-role-alignment.md`
