---
applyTo: "tests/**/*.py,.github/workflows/**/*.yml,pyproject.toml"
---

# Testing Instructions

Choose the smallest test scope that proves the change.

- use unit tests for isolated logic
- use integration tests when DB, DI, auth, or multi-layer behavior matters
- use current fixtures and CI behavior as the operational baseline
- add or update tests when behavior, contracts, or security-sensitive flows change
- do not assume CI runs every test path unless the workflow actually does

For auth and security changes, prefer more than unit coverage alone.
