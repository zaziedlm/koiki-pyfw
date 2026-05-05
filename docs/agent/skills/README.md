# Agent Skills

## Purpose

This directory contains the canonical Agent Skills for this repository.

Use these skills when the task already matches a known work type and you want concise, task-specific guidance.

## Skills

- `koiki-project-overview`
  - classify the task and choose the correct repository layer
- `koiki-app-feature-work`
  - implement business-specific backend changes under `components/koiki_ref_app/`
- `koiki-libkoiki-feature-work`
  - implement reusable framework changes under `components/libkoiki/`
- `koiki-auth-security`
  - handle auth, RBAC, SSO, SAML, and security-sensitive changes
- `koiki-testing`
  - choose and implement the right test scope

## Notes

- Shared cross-cutting guidance remains in `docs/agent/`.
- API ownership follows `docs/agent/boundaries.md`: reusable framework behavior belongs in `components/libkoiki/`, reference-app behavior belongs in `components/koiki_ref_app/`, and downstream customer-specific APIs start under `apps/`.
- The current Todo API is a `libkoiki` framework sample / starter capability, not precedent for placing new business APIs in `components/libkoiki/`.
- Skill-specific metadata lives in each skill's `agents/openai.yaml`.
- Claude Code discovery wrappers live under `.claude/skills/`.
- `docs/agent/skills/` remains the canonical source for skill content.
- Future maintainer/template role alignment is tracked in `future-role-alignment.md`.
