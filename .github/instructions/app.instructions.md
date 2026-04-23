---
applyTo: "app/**/*.py,app/**/*.toml,components/koiki_ref_app/**/*.py,components/koiki_ref_app/**/*.toml"
---

# app Instructions

This scope is for application-specific backend behavior.

- keep business-specific logic, integrations, and composition here
- reuse `components/libkoiki` capabilities before extending shared framework code
- follow the current `components/koiki_ref_app/src/koiki_ref_app/api/v1/` structure and keep `app/main.py` as a compatibility wrapper
- add only the layers needed for the feature
- validate application behavior and affected integration points

Do not duplicate framework behavior in `components/koiki_ref_app` when a shared solution already exists in `components/libkoiki`.
