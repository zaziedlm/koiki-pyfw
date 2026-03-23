# Agent Guidance Migration

## Purpose

This note tracks the migration from draft agent guidance to the canonical repository layout.

For the steady-state design and maintenance model after migration, see `docs/dev/agent-guidance-design.md`.

## Status Snapshot

As of 2026-03-23, the migration status is:

- completed: canonical shared guidance under `docs/agent/`
- completed: canonical skills under `docs/agent/skills/`
- completed: Claude Code skill discovery wrappers under `.claude/skills/`
- completed: root and local entry files for `AGENTS.md` and `CLAUDE.md`
- completed: GitHub Copilot guidance under `.github/`
- completed: final review of the shortened root `CLAUDE.md`
- completed: deletion of the former draft guidance area after approval
- completed: bundled official validator run for canonical and Claude wrapper skills

## Canonical Locations

- shared guidance: `docs/agent/`
- skills: `docs/agent/skills/`
- Claude Code skill wrappers: `.claude/skills/`
- root and directory entry files: `AGENTS.md`, `CLAUDE.md`, `app/AGENTS.md`, `app/CLAUDE.md`, `libkoiki/AGENTS.md`, `libkoiki/CLAUDE.md`
- GitHub Copilot guidance: `.github/copilot-instructions.md`
- scoped Copilot instructions: `.github/instructions/*.instructions.md`

## Root CLAUDE Migration

The previous root `CLAUDE.md` was a long mixed document containing:

- historical security update notes
- environment and dependency guidance
- operational architecture notes

The canonical migration approach is:

1. keep root `CLAUDE.md` short as an entry file
2. move durable operational guidance into `docs/agent/`
3. preserve historical detail in git history unless a specific section is still operationally required

Do not copy the old root `CLAUDE.md` back into the canonical entry file wholesale.

## Migration Coverage

The following draft assets have canonical replacements:

- shared docs: `index.md`, `boundaries.md`, `architecture.md`, `app.md`, `libkoiki.md`, `auth-security.md`, `testing.md`
- entry files: `ROOT_AGENTS.md`, `ROOT_CLAUDE.md`, `app_AGENTS.md`, `app_CLAUDE.md`, `libkoiki_AGENTS.md`, `libkoiki_CLAUDE.md`
- Copilot files: `copilot-instructions.md`, `*.instructions.md`
- skills: all 5 draft skills, plus `agents/openai.yaml` metadata in the canonical copies
- Claude adapters: matching thin wrappers for all 5 skills under `.claude/skills/`

The draft area is no longer needed because canonical coverage is complete.

## Validation Performed

The bundled official validator was run for:

- canonical skills under `docs/agent/skills/`
- Claude Code wrapper skills under `.claude/skills/`

The validation confirmed the skill folders are valid. Additional local checks also verified:

- each skill directory contains `SKILL.md`
- frontmatter `name` exists and matches the directory name
- canonical skills include `agents/openai.yaml`
- Claude wrapper skills reference canonical skill paths

## Next Plan

1. keep canonical guidance aligned as skills evolve
2. rerun the bundled official validator when future skills or wrappers are added

## Retirement Conditions

The former retirement conditions were satisfied:

1. canonical files are reviewed and accepted
2. repository references point to canonical paths
3. skill metadata has been validated
