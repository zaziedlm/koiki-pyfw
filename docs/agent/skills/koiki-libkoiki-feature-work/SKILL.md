---
name: koiki-libkoiki-feature-work
description: Use when adding or modifying reusable framework capabilities under libkoiki/, including shared API patterns, services, repositories, schemas, configuration, security, and infrastructure behavior.
---

# KOIKI libkoiki Feature Work

Use this skill when the requested change belongs in the reusable framework layer.

## Scope

Target directories include:

- `libkoiki/api/`
- `libkoiki/core/`
- `libkoiki/services/`
- `libkoiki/repositories/`
- `libkoiki/models/`
- `libkoiki/schemas/`
- `libkoiki/db/`

## Workflow

1. confirm the feature is reusable and not business-specific
2. find the existing layer pattern closest to the request
3. apply changes in layer order, starting from models/schemas only if needed
4. keep interfaces consistent with existing DI and transaction patterns
5. check whether app-facing behavior or tests must be updated

## Guardrails

- do not place business-specific rules in `libkoiki/`
- do not bypass the service layer with endpoint-specific data logic unless an existing pattern already does so
- do not introduce new cross-cutting mechanisms if an existing core module already owns that concern

## Validate

- affected unit tests under `tests/unit/libkoiki/`
- relevant integration coverage when behavior crosses DB, auth, or middleware boundaries

## Read Next

- `docs/agent/libkoiki.md`
- `docs/agent/architecture.md`
- `docs/agent/boundaries.md`
- `docs/agent/testing.md`
- `docs/agent/auth-security.md`
- `references/framework-patterns.md`
