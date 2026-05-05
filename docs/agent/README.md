# Agent Guide Index

## Purpose

This directory contains the shared, tool-neutral guidance for AI agents working in this repository.

Use these documents as the primary operational guidance before relying on older tool-specific files or historical design notes.

## Read Order

Start here when the task is not yet classified.

1. `boundaries.md`
   - decide whether the change belongs in `components/libkoiki/` or `components/koiki_ref_app/`
2. `architecture.md`
   - understand the repository structure and preferred layer flow
3. `environment.md`
   - account for agent-specific environment collisions before running validation
4. `testing.md`
   - choose the correct validation scope
5. `auth-security.md`
   - read for auth, permission, SSO, SAML, or security-sensitive work
6. `libkoiki.md`
   - read for reusable framework changes
7. `app.md`
   - read for business-specific application changes

## Operational Principles

- Current implementation is the primary source of truth.
- Shared agent docs are the operational guidance layer.
- Historical design documents are reference material.
- Tool-specific entry files should remain short and should point back to this directory.

## Main Repository Split

- `components/libkoiki/`: reusable framework behavior
- `components/koiki_ref_app/`: reference application backend behavior
- `app/`: compatibility wrapper
- `frontend/`: frontend implementation
- `tests/`: validation
- `docs/`: human-oriented documentation

## Task Routing

Use these routes when the task is already clear.

- framework capability or shared backend concern -> `libkoiki.md`
- business feature or project-specific backend behavior -> `app.md`
- auth, RBAC, token, SSO, or SAML change -> `auth-security.md`
- uncertain placement -> `boundaries.md`
- uncertain test scope -> `testing.md`

## Skills

Canonical skills live under `docs/agent/skills/`.
Use the project-overview skill first when task routing is still ambiguous.

## Maintainer Notes

For the design intent and maintenance model behind this guidance system, see:

- `docs/dev/agent-guidance-design.md`
- `docs/dev/agent-guidance-migration.md`
