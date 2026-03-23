# AGENTS.md

This directory is the application-specific backend layer.

Read first:

- `../docs/agent/boundaries.md`
- `../docs/agent/architecture.md`
- `../docs/agent/app.md`
- `../docs/agent/testing.md`

Read when relevant:

- `../docs/agent/auth-security.md`

Use this directory for:

- business-specific APIs
- application services and repositories
- project-specific integrations such as SSO and SAML
- application-level composition of `libkoiki/` behavior

Before changing code in this directory:

- confirm the behavior is specific to this application
- reuse `libkoiki/` capabilities before adding new framework logic
- follow the existing `app/api/v1/` and `app/main.py` structure
- validate application behavior and affected integration points
