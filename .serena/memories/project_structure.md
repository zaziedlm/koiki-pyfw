# プロジェクト構造

## 現行の正本

```
koiki-pyfw/
├── pyproject.toml          # uv workspace / tool settings
├── uv.lock                 # dependency lockfile source of truth
├── alembic.ini             # migration configuration
├── components/
│   ├── libkoiki/           # reusable framework package
│   └── koiki_ref_app/      # reference application package
├── app/                    # compatibility wrapper for legacy app imports
├── frontend/               # Next.js frontend starter
├── tests/                  # root shared / integration tests
├── docs/                   # documentation
└── ops/                    # operational helpers
```

## components/libkoiki

Reusable framework code lives under `components/libkoiki/src/libkoiki`.

Typical responsibilities:

- framework API composition
- auth, config, middleware, logging, monitoring
- database session and transaction infrastructure
- framework models, schemas, repositories, and services
- framework tests under `components/libkoiki/tests`

## components/koiki_ref_app

Reference application code lives under `components/koiki_ref_app/src/koiki_ref_app`.

Typical responsibilities:

- application factory and ASGI entrypoint
- app-specific bootstrap
- SSO / SAML integration for the reference application
- todo reference domain
- app tests under `components/koiki_ref_app/tests`

The current ASGI entrypoint is `koiki_ref_app.asgi:app`.

## app

The root `app/` directory is a compatibility wrapper for older imports and `app.main:app`.
Do not place new application implementation here unless explicitly maintaining compatibility.

## frontend

`frontend/` is the Next.js starter frontend. It remains at the repository root.

## tests

Root `tests/` is for shared, cross-component, or repository-level tests.
Component-owned tests should live under the matching component package where practical.

## docs

Current operational docs should describe `uv`, `uv.lock`, `components/libkoiki`,
`components/koiki_ref_app`, and `koiki_ref_app.asgi:app`.
Historical plans may still mention Poetry or old paths when clearly treated as history.
