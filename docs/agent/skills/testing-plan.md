# Agent Skill Test Plan

## Purpose

This document defines how to test whether repository Agent Skills remain discoverable and are selected for the right kinds of tasks.

Use it when:

- adding or changing a canonical skill under `docs/agent/skills/`
- updating Claude discovery wrappers under `.claude/skills/`
- changing OpenAI skill metadata under `agents/openai.yaml`
- reviewing whether current prompts still route to the intended skill

## Test Layers

Split validation into two layers.

### 1. Repository-side contract tests

These checks run inside this repository and should stay in CI.

They validate:

- every canonical skill directory exists
- each canonical skill contains `SKILL.md`
- each canonical skill contains `agents/openai.yaml`
- `SKILL.md` frontmatter `name` matches the directory name
- OpenAI metadata includes the expected interface fields
- the default prompt references the correct `$skill-name`
- each Claude wrapper points to the canonical skill path
- the prompt case catalog remains well formed and covers every skill

Run:

```bash
uv run --locked pytest tests/unit/agent_guidance/
```

### 2. Agent-routing smoke tests

These checks verify actual runtime behavior in an agent-capable environment.

They validate:

- the intended skill is selected for a representative prompt
- obviously wrong skills are not selected first
- multi-skill cases still include the required security or testing skill
- ambiguous requests start with `koiki-project-overview`
- where required, the first selected skill matches the expected routing order

The repository keeps the prompt catalog for these checks at:

- `tests/unit/agent_guidance/prompt_cases.yaml`

Use the prompt text in that catalog as the regression suite for manual or external-harness runs.
For each case, record `observed_skills` in the order the runtime selected them.

Generate a manual checklist:

```bash
uv run --locked python scripts/agent_skill_smoke.py generate
```

On Windows PowerShell, prefer direct UTF-8 file output to avoid console-pipeline encoding issues:

```bash
uv run --locked python scripts/agent_skill_smoke.py generate --output agent-skill-checklist.md
```

Generate an empty results template:

```bash
uv run --locked python scripts/agent_skill_smoke.py template
```

Windows PowerShell:

```bash
uv run --locked python scripts/agent_skill_smoke.py template --output agent-skill-results.json
```

Evaluate recorded results:

```bash
uv run --locked python scripts/agent_skill_smoke.py evaluate --results agent-skill-results.json
```

## Recommended Smoke Cases

The prompt catalog already includes the minimum representative cases:

- ambiguous layer selection
- app-specific business feature work
- reusable `components/libkoiki/` framework work
- auth and RBAC changes
- app-specific SSO/SAML changes
- framework-level security changes
- test-scope and CI-scope decisions
- frontend-only work that should fall back to overview first

## Change Policy

Update the prompt catalog when:

- a new skill is added
- a skill scope changes materially
- adapters or metadata change in a way that could affect discovery
- a real routing mistake is found and needs regression coverage

## Limits

The contract tests in this repository do not prove actual LLM runtime routing by themselves.

They are intended to:

- catch broken metadata or adapter drift early
- keep a stable routing expectation catalog in version control
- give external or manual smoke tests a fixed prompt set
