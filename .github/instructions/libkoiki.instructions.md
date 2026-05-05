---
applyTo: "components/libkoiki/**/*.py,components/libkoiki/**/*.toml"
---

# libkoiki Instructions

This scope is for reusable framework behavior.

- place shared auth, config, middleware, persistence, schema, and service behavior here
- do not place business-specific rules here
- keep API behavior here only when it is reusable framework behavior or an explicit starter/sample capability
- treat the current Todo API as a framework sample / starter capability, not as precedent for new business APIs
- extend current framework patterns before adding new abstractions
- check whether `components/koiki_ref_app` composes the changed contract
- validate at framework and integration scope when shared behavior changes

If reusability is unclear, prefer keeping the change out of `components/libkoiki` until the abstraction is justified.
