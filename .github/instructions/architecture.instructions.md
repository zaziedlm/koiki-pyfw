---
applyTo: "main.py,app/**/*.py,components/libkoiki/**/*.py,components/koiki_ref_app/**/*.py,components/koiki_ref_app/alembic/**/*.py,tests/**/*.py"
---

# Architecture Instructions

Apply the existing backend structure before creating new abstractions.

- preserve the split between `components/libkoiki` and `components/koiki_ref_app`
- route downstream or customer-specific API behavior to `apps/` unless it is clearly reusable framework behavior or reference-app starter behavior
- treat the current Todo API as a `libkoiki` framework sample / starter capability, not as a placement precedent for new business APIs
- prefer the layered flow: API -> Service -> Repository -> Model/Schema -> Core/Infrastructure
- keep lower layers independent from higher layers
- reuse the nearest existing pattern before inventing a parallel structure
- keep cross-cutting concerns explicit, especially auth, logging, monitoring, middleware, and transaction handling

When architecture guidance conflicts with older documents, prefer current implementation and shared agent docs.
