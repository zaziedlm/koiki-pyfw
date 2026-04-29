---
name: koiki-app-feature-work
description: Use when implementing business-specific functionality under components/koiki_ref_app/, including domain endpoints, services, repositories, models, schemas, and application-specific integrations built on components/libkoiki.
---

# KOIKI app Feature Work

Use this skill for business-application behavior that should remain separate from the framework.

## Scope

Typical targets:

- `components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/`
- `components/koiki_ref_app/src/koiki_ref_app/api/v1/router.py`
- `components/koiki_ref_app/src/koiki_ref_app/services/`
- `components/koiki_ref_app/src/koiki_ref_app/repositories/`
- `components/koiki_ref_app/src/koiki_ref_app/models/`
- `components/koiki_ref_app/src/koiki_ref_app/schemas/`
- `components/koiki_ref_app/src/koiki_ref_app/core/`

## Workflow

1. confirm the request is business-specific or application-specific
2. reuse `components/libkoiki/` capabilities before adding new application code
3. add or extend endpoint, service, repository, and schema layers only as needed
4. keep application code thin where framework behavior already exists
5. check whether migrations, config, or frontend contracts are affected

## Guardrails

- do not reimplement generic auth, user, or infrastructure behavior that already exists in `components/libkoiki/`
- do not push business-specific assumptions down into shared framework code
- do not create parallel patterns if a nearby app module already establishes the local convention

## Validate

- app-focused tests first
- endpoint behavior for changed routes
- integration points with `components/libkoiki/` when the feature composes shared services

## Read Next

- `docs/agent/app.md`
- `docs/agent/architecture.md`
- `docs/agent/boundaries.md`
- `docs/agent/testing.md`
- `docs/agent/auth-security.md`
- `references/app-extension-patterns.md`
