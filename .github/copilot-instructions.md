# GitHub Copilot Instructions

This repository separates reusable framework behavior from application-specific backend behavior.

- `components/libkoiki/` is the reusable backend framework layer
- `components/koiki_ref_app/` is the current reference application backend layer
- `app/` is a compatibility wrapper
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

- keep reusable framework behavior in `components/libkoiki/`
- keep business-specific behavior in `components/koiki_ref_app/`
- start downstream or customer-specific API behavior under `apps/` unless it is clearly reusable framework behavior or reference-app starter behavior
- treat the current Todo API as a `libkoiki` framework sample / starter capability, not as precedent for new business APIs
- follow the existing layered structure before introducing new patterns
- validate changes at the smallest scope that proves the behavior
- treat historical design documents as reference material, not operational truth
