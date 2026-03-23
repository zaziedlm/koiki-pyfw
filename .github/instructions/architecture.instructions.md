---
applyTo: "main.py,app/**/*.py,libkoiki/**/*.py,tests/**/*.py,alembic/**/*.py"
---

# Architecture Instructions

Apply the existing backend structure before creating new abstractions.

- preserve the split between `libkoiki/` and `app/`
- prefer the layered flow: API -> Service -> Repository -> Model/Schema -> Core/Infrastructure
- keep lower layers independent from higher layers
- reuse the nearest existing pattern before inventing a parallel structure
- keep cross-cutting concerns explicit, especially auth, logging, monitoring, middleware, and transaction handling

When architecture guidance conflicts with older documents, prefer current implementation and shared agent docs.
