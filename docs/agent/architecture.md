# Architecture

## Purpose

This repository follows a layered backend architecture built around a reusable framework layer and an application-specific layer.

The main goal is to keep framework concerns, business logic, and infrastructure concerns separate enough to remain maintainable and extensible.

## Main Structure

Core areas in the current repository:

- `components/libkoiki/`: reusable framework code
- `components/koiki_ref_app/`: reference application backend code
- `app/`: compatibility wrapper for legacy imports and entrypoints
- `frontend/`: application frontend
- `tests/`: unit and integration tests
- `docs/`: human-oriented design and development documentation

## Layered Flow

Prefer the following flow when implementing backend changes:

- API layer
- Service layer
- Repository layer
- Model / Schema layer
- Core / Infrastructure layer

Typical responsibility split:

- API: request handling, validation, response shaping, dependency wiring
- Service: business logic and use-case orchestration
- Repository: persistence and query behavior
- Model / Schema: DB structures and validated data contracts
- Core / Infrastructure: config, auth, middleware, logging, transactions, DB session management

## Dependency Direction

Prefer one-way dependencies:

- API depends on Service
- Service depends on Repository
- Repository depends on Model / DB access
- shared cross-cutting concerns may be used where appropriate

Do not make lower layers depend on higher layers.

## Extension Rules

Before adding a new module:

1. find the nearest existing pattern
2. extend the current structure before inventing a new one
3. keep framework behavior in `components/libkoiki/`
4. keep business behavior in `components/koiki_ref_app/`

Prefer modifying an existing extension point over creating parallel structure.

## Current Routing Structure

In the current codebase:

- framework routes are assembled under `components/libkoiki/src/libkoiki/api/v1/`
- reference application routes are assembled under `components/koiki_ref_app/src/koiki_ref_app/api/v1/`
- application startup and composition are centered in `components/koiki_ref_app/src/koiki_ref_app/`
- `app/main.py` exists as a compatibility wrapper

When adding new API behavior, follow the existing router composition style already used by the project.

## Cross-Cutting Concerns

These concerns should remain explicit and consistent:

- authentication and authorization
- configuration
- logging and monitoring
- database session and transaction handling
- rate limiting and security middleware

Do not hide cross-cutting behavior inside isolated feature code when a shared layer already owns that concern.

## Architecture Guardrails

Avoid:

- bypassing the service layer for non-trivial business behavior
- embedding persistence logic directly in endpoint code
- duplicating config, auth, or middleware logic in feature modules
- introducing new directory conventions without a strong reason

## Source Priority

When architecture descriptions conflict:

1. current implementation
2. shared agent docs
3. design references
