---
name: koiki-business-app-feature-work
description: Use when implementing downstream / customer-specific business backend APIs under apps/, composing components/libkoiki and components/koiki_ref_app without editing them. For upstream reference-application behavior under components/koiki_ref_app/, use koiki-refapp-feature-work instead.
---

# KOIKI Business App Feature Work

Use this skill for downstream, project-specific backend behavior that lives under `apps/`.

`apps/` is the downstream business-app layer. It composes the upstream framework (`components/libkoiki/`) and reference app (`components/koiki_ref_app/`) without editing them.

For upstream reference-application behavior under `components/koiki_ref_app/`, use `koiki-refapp-feature-work` instead.

## Scope

Typical targets:

- `apps/asgi.py`
- `apps/api/v1/router.py`
- `apps/api/v1/endpoints/`
- `apps/services/`
- `apps/repositories/`
- `apps/models/`
- `apps/schemas/`
- `apps/core/`

## Composition Rules

- the business-app ASGI entrypoint is owned by `apps/asgi.py`, built by composing `koiki_ref_app.app_factory.create_app()` and registering business routers with `include_router()`
- business-specific models inherit the shared `Base` from `koiki_ref_app.db.base`, which shares the `libkoiki.db.base.Base` registry / metadata so apps/ models stay on one unified migration target
- dependency direction is `apps/ -> components/` only; `components/` must not import `apps/`
- see `docs/dev/apps-plugin-composition-plan.ja.md` for the composition design

## DB Base Rule

- default: business-app models import `Base` from `koiki_ref_app.db.base` (shared registry/metadata, flexible common columns)
- exception: if a downstream app needs a different primary key shape, `tenant_id`, or different audit columns, define an apps-local base that shares `libkoiki.db.base.Base` registry instead of editing `components/` for business-only needs

## Workflow

1. confirm the request is downstream / customer-specific business behavior, not reusable framework or reference-app starter behavior
2. reuse `components/libkoiki/` and `components/koiki_ref_app/` capabilities before adding new code
3. add or extend `apps/` endpoint, service, repository, schema, and model layers only as needed
4. own router registration and ASGI composition in `apps/`, not in `components/`
5. check whether business-specific migrations, config, or frontend contracts are affected

## Guardrails

- do not edit `components/` to add business-app-specific APIs; keep business composition in `apps/`
- do not make `components/` import or depend on `apps/`
- promote a change out of `apps/` into `components/libkoiki/` or `components/koiki_ref_app/` only when it becomes clearly reusable starter/reference behavior
- do not treat the `libkoiki` Todo sample as precedent for placement decisions
- do not duplicate framework or reference-app behavior that already exists upstream

## Validate

- business-app-focused tests first
- `apps.asgi:app` imports and composes the reference app plus business routers
- no direct `components/` -> `apps/` import exists

## Read Next

- `apps/README.md`
- `docs/dev/apps-plugin-composition-plan.ja.md`
- `docs/agent/app.md`
- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/testing.md`
- `references/business-app-patterns.md`
- `docs/agent/skills/future-role-alignment.md`
