# CLAUDE.md

This directory contains reusable framework code.

Read first:

- @../../docs/agent/boundaries.md
- @../../docs/agent/architecture.md
- @../../docs/agent/libkoiki.md
- @../../docs/agent/testing.md

Working rules:

- keep this layer reusable
- avoid project-specific business assumptions
- follow the existing layered structure
- check downstream impact on `components/koiki_ref_app/`
- validate changes at the right scope for shared behavior
