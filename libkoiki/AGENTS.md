# AGENTS.md

This directory is the reusable framework layer.

Read first:

- `../docs/agent/boundaries.md`
- `../docs/agent/architecture.md`
- `../docs/agent/libkoiki.md`
- `../docs/agent/testing.md`

Use this directory for:

- shared backend capabilities
- reusable auth, config, middleware, logging, persistence, and schema behavior
- framework-level services, repositories, and API structure

Do not place business-specific behavior here unless it is clearly reusable beyond the current application.

Before changing code in this directory:

- confirm the behavior belongs in the framework layer
- extend existing patterns before creating new abstractions
- check whether `app/` composes the affected contract
- validate at the correct framework or integration scope
