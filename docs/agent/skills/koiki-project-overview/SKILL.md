---
name: koiki-project-overview
description: Use when you need to understand the repository structure, choose the correct layer for a change, or identify where framework code ends, application code begins, and downstream apps/ ownership may apply.
---

# KOIKI Project Overview

Use this skill first when the task is ambiguous or when the correct edit location is not yet clear.

## Focus

- determine whether the task belongs to `components/libkoiki/`, `components/koiki_ref_app/`, `apps/`, `frontend/`, or cross-cutting areas
- preserve the framework/application boundary
- route the task to a more specific skill after the initial classification

## Future Role Alignment

This skill is the transitional repository overview and routing skill. In a later maintainer/template split, it is the seed for a maintainer overview skill and should remain active until replacement overview skills exist.

## Decision Rules

- if the change is reusable across applications, prefer `components/libkoiki/` and route to `koiki-libkoiki-feature-work`
- if the change depends on reference-app business requirements, prefer `components/koiki_ref_app/` and route to `koiki-refapp-feature-work`
- if the change is downstream or customer-specific, place it under `apps/` and route to `koiki-business-app-feature-work`
- treat the current Todo API as a `libkoiki` framework sample / starter capability, not as precedent for new business APIs
- if the change affects UI integration or browser flows, inspect `frontend/`
- if the change affects auth, SSO, SAML, rate limiting, or audit behavior, also read the auth/security skill

> Note: `koiki-refapp-feature-work` (reference app, `components/koiki_ref_app/`) and `koiki-business-app-feature-work` (downstream apps, `apps/`) are distinct; do not conflate the singular reference app with the plural downstream apps directory.

## Read Next

- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`
- `docs/agent/auth-security.md`
- `docs/agent/testing.md`
- `docs/agent/skills/future-role-alignment.md`
