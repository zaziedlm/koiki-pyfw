---
name: koiki-project-overview
description: Use when you need to understand the repository structure, choose the correct layer for a change, or identify where framework code ends and application code begins.
---

# KOIKI Project Overview

Use this skill first when the task is ambiguous or when the correct edit location is not yet clear.

## Focus

- determine whether the task belongs to `libkoiki/`, `app/`, `frontend/`, or cross-cutting areas
- preserve the framework/application boundary
- route the task to a more specific skill after the initial classification

## Decision Rules

- if the change is reusable across applications, prefer `libkoiki/`
- if the change depends on business requirements, prefer `app/`
- if the change affects UI integration or browser flows, inspect `frontend/`
- if the change affects auth, SSO, SAML, rate limiting, or audit behavior, also read the auth/security skill

## Read Next

- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`
- `docs/agent/auth-security.md`
- `docs/agent/testing.md`
