---
applyTo: "app/**/*.py,app/**/*.toml"
---

# app Instructions

This scope is for application-specific backend behavior.

- keep business-specific logic, integrations, and composition here
- reuse `libkoiki/` capabilities before extending shared framework code
- follow the current `app/api/v1/` and `app/main.py` structure
- add only the layers needed for the feature
- validate application behavior and affected integration points

Do not duplicate framework behavior in `app/` when a shared solution already exists in `libkoiki/`.
