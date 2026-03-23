# GitHub Copilot Instructions

This repository separates reusable framework behavior from application-specific backend behavior.

- `libkoiki/` is the reusable backend framework layer
- `app/` is the current application-specific backend layer
- `frontend/` is the frontend implementation
- `tests/` contains unit and integration validation

Use current implementation as the primary source of truth.

Before making structural changes, read:

- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/testing.md`

Read these when relevant:

- `docs/agent/auth-security.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`

Core rules:

- keep reusable framework behavior in `libkoiki/`
- keep business-specific behavior in `app/`
- follow the existing layered structure before introducing new patterns
- validate changes at the smallest scope that proves the behavior
- treat historical design documents as reference material, not operational truth
