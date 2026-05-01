# Agent Skill Future Role Alignment

## Purpose

This document records the v0.7 skill follow-up decisions without renaming or removing the current skills.

The current skills remain the active discovery surface. Future maintainer/template roles are alignment targets for later extraction, not replacement names for current work.

## Current Skill Mapping

| Current skill | Current role | Future role alignment | Notes |
| --- | --- | --- | --- |
| `koiki-project-overview` | Repository routing and layer classification | Transitional overview / future maintainer overview seed | Keep as the first stop for ambiguous tasks until separate maintainer and template overviews exist. |
| `koiki-libkoiki-feature-work` | Reusable framework implementation | Maintainer framework work | This is already the closest match to the future maintainer-facing framework skill. |
| `koiki-app-feature-work` | Reference application backend implementation | Template backend work | This should remain focused on `components/koiki_ref_app` and avoid customer-specific app behavior. |
| `koiki-auth-security` | Auth, SSO, SAML, RBAC, security logging | Cross-cutting security skill | Retain across maintainer and template phases because security behavior spans both layers. |
| `koiki-testing` | Test scope and validation guidance | Cross-cutting testing skill | Retain across maintainer and template phases because validation choices span both layers. |

## Phase A Status

Phase A preserves the current skills and annotates their future intent.

Completed decisions:

- current skill names remain active
- Claude wrappers remain thin adapters to canonical skills
- no existing skill is deleted or renamed
- current-to-future role mapping is documented above
- individual `SKILL.md` files include a short future role note

## Phase B Design

Phase B is a future split design. It should not be implemented until the template boundaries have stayed stable in normal work.

Maintainer-oriented skill candidates:

- `koiki-maintainer-overview`
  - route upstream maintenance work across framework, template backend, frontend starter, CI, Docker, and docs
- `koiki-maintainer-framework-work`
  - evolve reusable `components/libkoiki` framework behavior
- `koiki-maintainer-template-backend-work`
  - evolve upstream `components/koiki_ref_app` starter behavior
- `koiki-maintainer-template-frontend-work`
  - evolve upstream root `frontend/` starter behavior

Template-oriented skill candidates:

- `koiki-template-overview`
  - guide copy-first template adoption and boundaries
- `koiki-template-backend-feature-work`
  - guide downstream backend work derived from `components/koiki_ref_app`
- `koiki-template-frontend-feature-work`
  - guide downstream frontend work derived from root `frontend/`

Cross-cutting skills to retain:

- auth/security guidance
- testing guidance

## Frontend Template Responsibility

Root `frontend/` is the upstream starter frontend paired with `components/koiki_ref_app`.

Future template frontend guidance should cover:

- UI starter conventions and route structure
- API client and auth integration expectations
- BFF / browser-flow contracts when present
- when a frontend change belongs in upstream `frontend/`
- when project-specific frontend code should live under `apps/<project-slug>/frontend/`

It should not treat root `frontend/` as part of the reusable Python framework package.

## Migration Rules

- Do not replace current skill names until replacement skills exist and wrappers are validated.
- Do not split cross-cutting security or testing guidance prematurely.
- Keep old-to-new role mapping visible while both naming schemes are in use.
- Add consumer-oriented skills only after copy-first template adoption has concrete downstream examples.
