# Business App Patterns Reference

Use this reference when the `koiki-business-app-feature-work` skill needs a compact reminder of downstream `apps/` composition patterns.

## Focus Areas

- downstream / customer-specific API, service, repository, model, and schema wiring under `apps/`
- composing `koiki_ref_app.app_factory.create_app()` in `apps/asgi.py` and registering business routers with `include_router()`
- reusing `components/libkoiki/` and `components/koiki_ref_app/` capabilities before adding new code
- keeping the dependency direction `apps/ -> components/` only

## DB Base

- default: business-app models import `Base` from `koiki_ref_app.db.base`, which shares the `libkoiki.db.base.Base` registry / metadata
- this keeps `apps/` models on one unified migration target without editing `components/`
- exception: if a downstream app needs a different primary key, `tenant_id`, or different audit columns, define an apps-local base sharing `libkoiki.db.base.Base` registry rather than changing shared framework or reference-app code

## Source Material

Primary source material comes from:

- `apps/README.md`
- `docs/dev/apps-plugin-composition-plan.ja.md`
- current `components/koiki_ref_app/src/koiki_ref_app/app_factory.py` and `components/koiki_ref_app/src/koiki_ref_app/db/base.py`
- shared agent docs in `docs/agent/`

## Practical Reminder

Before adding code under `apps/`, confirm both of these:

- the behavior is downstream / customer-specific, not reusable framework or reference-app starter behavior
- the feature composes existing `components/` capabilities instead of duplicating them
