# Agent Guidance Design

## Purpose

This document explains the design and maintenance model for the repository's rule files and Agent Skills.

Use it when you need to understand:

- why the guidance is split across multiple locations
- which files are canonical versus tool-specific adapters
- how to extend the system without adding unnecessary complexity

## Design Goal

The repository guidance should work well for multiple agent tools while keeping one canonical source of truth.

The priority order is:

1. Codex
2. Claude Code
3. GitHub Copilot

The design therefore favors:

- canonical shared guidance in repository docs
- short entry files and thin adapters for individual tools
- minimal duplication
- clear skill discovery paths

## Core Concept

The guidance system is split into two layers:

- rules
  - stable operational guidance about architecture, boundaries, testing, and security
- skills
  - task-shaped guidance for recurring work types

Rules answer:

- how this repository should be changed
- where code belongs
- what constraints must be preserved

Skills answer:

- how to approach a specific category of work
- what related guidance to load next

## Canonical Sources

These files are the source of truth:

- `docs/agent/`
  - canonical shared guidance
- `docs/agent/skills/`
  - canonical skill content

These canonical files should contain the durable content.
Tool-specific files should point back to them instead of re-explaining the same rules.

## Tool Adapters

The repository supports three adapter surfaces.

### Codex

Primary entry points:

- `AGENTS.md`
- `app/AGENTS.md`
- `libkoiki/AGENTS.md`

Role:

- provide the first read path for Codex-style agents
- stay short
- point into `docs/agent/`

### Claude Code

Primary entry points:

- `CLAUDE.md`
- `app/CLAUDE.md`
- `libkoiki/CLAUDE.md`
- `.claude/skills/`

Role:

- use Claude Code's native `@path` import behavior
- keep `CLAUDE.md` thin and import canonical guidance
- provide skill discovery wrappers under `.claude/skills/`

Important constraint:

- `.claude/skills/` is an adapter layer, not the canonical authoring location

### GitHub Copilot

Primary entry points:

- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `AGENTS.md`

Role:

- provide repository-wide and path-specific instructions
- keep repository-wide instructions minimal
- use path-specific files only for scoped behavior

## Why This Structure

This structure exists to avoid two common failure modes:

- duplicated rules drifting across tools
- overfitting the repository to one agent product

By keeping canonical guidance in `docs/agent/`, the repository can evolve once and expose thin compatibility layers for each tool.

## Current Skill Set

The current canonical skills are:

- `koiki-project-overview`
- `koiki-app-feature-work`
- `koiki-libkoiki-feature-work`
- `koiki-auth-security`
- `koiki-testing`

These skills were chosen because they map to recurring repository work patterns rather than one-off tasks.

## Maintenance Rules

When updating the guidance system:

1. edit canonical content first
2. update tool adapters only if the canonical change affects discovery or entry flow
3. keep adapter files short
4. do not duplicate long-form guidance into `AGENTS.md`, `CLAUDE.md`, or Copilot files
5. rerun skill validation after changing skill frontmatter or structure

## When To Add A New Skill

Add a new skill only when all of the following are true:

- the work type recurs
- the workflow is meaningfully different from existing skills
- the skill improves task routing or reduces repeated re-discovery

Do not create a new skill just to mirror a single feature area if an existing skill already covers the layer and workflow.

## When To Add A New Rule File

Add a new shared rule file only when:

- the guidance is cross-cutting
- it is stable enough to deserve durable documentation
- it does not fit naturally inside an existing shared doc

Prefer expanding an existing file over creating many narrow files.

## Validation Standard

The guidance system is considered healthy when:

- canonical shared docs exist under `docs/agent/`
- canonical skills exist under `docs/agent/skills/`
- Claude discovery wrappers exist under `.claude/skills/`
- entry files remain short and aligned
- the bundled skill validator passes for canonical and wrapper skills

## Related Documents

- `docs/agent/README.md`
- `docs/agent/skills/README.md`
- `docs/dev/agent-guidance-migration.md`
