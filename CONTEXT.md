# KOIKI-FW Context

KOIKI-FW separates reusable framework behavior, its reference application, and downstream business application backend composition. This glossary records the repository-specific terms used to keep those boundaries clear.

## Language

**Business App (`apps/`)**:
The downstream backend composition layer for customer- or project-specific APIs, services, models, schemas, router registration, and ASGI composition.
_Avoid_: frontend location, full-stack application directory

**Reference Frontend (`frontend/`)**:
The upstream Vite + React SPA starter paired with the reference application. It is the repository's frontend implementation location and is not part of `apps/`.
_Avoid_: Business App frontend, `apps/<project>/frontend/`

**Frontend Standard**:
Vite + React SPA is the current recommended frontend implementation style. Its API, authentication, and security contracts remain applicable to a future frontend technology unless that technology has an explicitly different contract.
_Avoid_: Vite + React as the only permitted frontend technology

**Frontend Contract**:
The API-facing agreement a frontend must observe, including endpoint schemas, authentication and authorization behavior, Cookie/CSRF requirements, error handling, and validation expectations.
_Avoid_: frontend placement rule
