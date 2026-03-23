---
name: koiki-testing
description: Use when adding, updating, or validating tests for libkoiki/ or app/, including unit, integration, fixture, and CI-scope decisions.
---

# KOIKI Testing

Use this skill when implementing tests or deciding the correct test scope.

## Focus

- choose the smallest test level that proves the change
- keep framework and application test intent separated
- align changes with current fixture and CI behavior

## Workflow

1. decide whether the change is unit, integration, or cross-layer
2. place tests near the affected responsibility
3. reuse existing fixtures before adding new ones
4. cover regressions introduced by the change, not every possible path
5. check whether CI scope already covers the new test

## Guardrails

- do not add integration tests when a unit test is sufficient
- do not mock away the behavior under test
- do not assume CI runs every test path; confirm what the workflow actually executes

## Validate

- the new or updated tests fail before the fix when practical
- the chosen test layer matches the changed responsibility

## Read Next

- `docs/agent/testing.md`
- `docs/agent/boundaries.md`
- `docs/agent/architecture.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`
- `docs/agent/auth-security.md`
