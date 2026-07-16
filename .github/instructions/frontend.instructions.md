---
applyTo: "frontend/**"
---

# Frontend Instructions

root `frontend/` is the reference Vite + React SPA. It consumes backend APIs but does not own backend API placement, authorization, Cookie issuance, refresh, logout, or CSRF validation.

- use `docs/frontend-spa-implementation-guide.ja.md` as the current frontend implementation guide
- use `docs/agent/skills/koiki-frontend-work/SKILL.md` for the frontend workflow and backend-skill handoff
- use feature API functions and TanStack Query hooks instead of duplicating HTTP transport in UI components
- preserve `credentials: "include"` and the backend-managed Cookie/CSRF session contract
- do not store access or refresh tokens in browser storage
- treat route guards as UX only; backend authorization remains mandatory
- add focused frontend coverage when schema, status/error behavior, mutation invalidation, or auth/CSRF handling changes

`apps/` is a backend-only business composition layer. Do not add frontend code or a frontend placement convention under `apps/`.
