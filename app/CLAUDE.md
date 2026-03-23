# CLAUDE.md

This directory contains application-specific backend code built on top of `libkoiki/`.

Read first:

- @../docs/agent/boundaries.md
- @../docs/agent/architecture.md
- @../docs/agent/app.md
- @../docs/agent/testing.md

Read when relevant:

- @../docs/agent/auth-security.md

Working rules:

- keep business-specific behavior in `app/`
- reuse shared framework capabilities before extending them
- follow the current `app/api/v1/` and `app/main.py` structure
- validate route, service, auth, and integration behavior at the appropriate scope
