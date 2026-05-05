# CLAUDE.md

This directory contains reference application backend code built on top of `components/libkoiki/`.

Read first:

- @../../docs/agent/boundaries.md
- @../../docs/agent/architecture.md
- @../../docs/agent/app.md
- @../../docs/agent/testing.md

Read when relevant:

- @../../docs/agent/auth-security.md

Working rules:

- keep business-specific behavior in `components/koiki_ref_app/`
- reuse shared framework capabilities before extending them
- follow the current `src/koiki_ref_app/api/v1/` and `src/koiki_ref_app/main.py` structure
- validate route, service, auth, and integration behavior at the appropriate scope
