---
name: koiki-libkoiki-feature-work
description: Use when adding or modifying reusable framework capabilities under components/libkoiki/, including shared API patterns, starter/sample capabilities, services, repositories, schemas, configuration, security, and infrastructure behavior.
---

# KOIKI libkoiki Feature Work

Use this skill when the requested change belongs in the reusable framework layer.

## Scope

Target directories include:

- `components/libkoiki/src/libkoiki/api/`
- `components/libkoiki/src/libkoiki/core/`
- `components/libkoiki/src/libkoiki/services/`
- `components/libkoiki/src/libkoiki/repositories/`
- `components/libkoiki/src/libkoiki/models/`
- `components/libkoiki/src/libkoiki/schemas/`
- `components/libkoiki/src/libkoiki/db/`

## Future Role Alignment

This skill aligns with future maintainer framework work. It should continue to own reusable `components/libkoiki` behavior until a dedicated maintainer framework skill is introduced.

## Workflow

1. confirm the feature is reusable and not business-specific
2. find the existing layer pattern closest to the request
3. apply changes in layer order, starting from models/schemas only if needed
4. keep interfaces consistent with existing DI and transaction patterns
5. check whether app-facing behavior or tests must be updated

## Guardrails

- do not place business-specific rules in `components/libkoiki/`
- only keep API behavior in `components/libkoiki/` when it is reusable framework behavior or an explicit starter/sample capability
- treat Todo as the current starter/sample exception, not as precedent for new business-specific APIs
- do not bypass the service layer with endpoint-specific data logic unless an existing pattern already does so
- do not introduce new cross-cutting mechanisms if an existing core module already owns that concern

## Validate

- affected unit tests under `components/libkoiki/tests/`
- relevant integration coverage when behavior crosses DB, auth, or middleware boundaries

## Read Next

- `docs/agent/libkoiki.md`
- `docs/agent/architecture.md`
- `docs/agent/boundaries.md`
- `docs/agent/testing.md`
- `docs/agent/auth-security.md`
- `references/framework-patterns.md`
- `docs/agent/skills/future-role-alignment.md`
