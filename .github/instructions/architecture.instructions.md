---
applyTo: "main.py,app/**/*.py,components/libkoiki/**/*.py,components/koiki_ref_app/**/*.py,components/koiki_ref_app/alembic/**/*.py,tests/**/*.py"
---

# Architecture Instructions

Apply the existing backend structure before creating new abstractions.

- preserve the split between `components/libkoiki` and `components/koiki_ref_app`
- prefer the layered flow: API -> Service -> Repository -> Model/Schema -> Core/Infrastructure
- keep lower layers independent from higher layers
- reuse the nearest existing pattern before inventing a parallel structure
- keep cross-cutting concerns explicit, especially auth, logging, monitoring, middleware, and transaction handling

When architecture guidance conflicts with older documents, prefer current implementation and shared agent docs.
