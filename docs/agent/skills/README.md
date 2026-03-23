# Agent Skills

## Purpose

This directory contains the canonical Agent Skills for this repository.

Use these skills when the task already matches a known work type and you want concise, task-specific guidance.

## Skills

- `koiki-project-overview`
  - classify the task and choose the correct repository layer
- `koiki-app-feature-work`
  - implement business-specific backend changes under `app/`
- `koiki-libkoiki-feature-work`
  - implement reusable framework changes under `libkoiki/`
- `koiki-auth-security`
  - handle auth, RBAC, SSO, SAML, and security-sensitive changes
- `koiki-testing`
  - choose and implement the right test scope

## Notes

- Shared cross-cutting guidance remains in `docs/agent/`.
- Skill-specific metadata lives in each skill's `agents/openai.yaml`.
- Claude Code discovery wrappers live under `.claude/skills/`.
- `docs/agent/skills/` remains the canonical source for skill content.
