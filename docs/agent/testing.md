# Testing

## Purpose

Tests should prove behavior changes at the smallest reasonable scope while preserving confidence for framework, application, and security-sensitive changes.

## Test Levels

Prefer the smallest test level that can prove the change.

- unit tests: isolated logic, fast feedback, mocked dependencies where appropriate
- integration tests: API, DB, auth, or multi-layer behavior
- end-to-end tests: full-user-flow verification when integration coverage is not enough

Do not start with end-to-end coverage when unit or integration coverage is sufficient.

## Placement Rules

Place tests near the responsibility they validate.

- framework behavior -> `components/libkoiki/tests/` or matching integration paths
- application behavior -> `components/koiki_ref_app/tests/` or matching integration paths
- cross-layer behavior -> integration tests

Use the current project structure before creating new test directories.

## Change Expectations

Add or update tests when:

- behavior changes
- a regression is fixed
- a new endpoint or service path is introduced
- auth, permission, token, SSO, or SAML behavior changes
- repository or transaction behavior changes in a meaningful way

## Current Reality

Use the actual repository setup as the operational baseline.

- current fixtures and overrides in `tests/conftest.py` matter more than generic examples
- current CI behavior matters more than idealized full-suite assumptions
- if CI only runs a subset, do not assume all tests are automatically enforced

## Test Selection Heuristic

Use unit tests when:

- logic is local to one service or helper
- DB behavior is not the thing being validated
- failure modes can be proven with mocks safely

Use integration tests when:

- DB state matters
- dependency injection wiring matters
- authentication or authorization behavior matters
- multiple layers must cooperate for the behavior to exist

## Security-Sensitive Changes

For auth and security-related changes, do not rely on unit tests alone.

Prefer a mix of:

- focused unit coverage for local logic
- integration coverage for request, token, permission, redirect, or session behavior

## Guardrails

Avoid:

- mocking the exact behavior under test
- adding integration tests when a unit test would prove the change
- assuming CI covers paths that the workflow does not actually run
- skipping tests for auth or boundary-sensitive changes without a clear reason

## Validation Standard

A change is not well validated unless the chosen test scope matches the actual risk introduced by the change.
