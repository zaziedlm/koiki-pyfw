# libkoiki

## Purpose

This document defines how to work in `components/libkoiki/`, the reusable framework layer of this repository.

Use this document when adding or changing shared backend capabilities that should remain reusable beyond the current application.

## Scope

Typical areas include:

- `components/libkoiki/src/libkoiki/api/`
- `components/libkoiki/src/libkoiki/core/`
- `components/libkoiki/src/libkoiki/db/`
- `components/libkoiki/src/libkoiki/models/`
- `components/libkoiki/src/libkoiki/schemas/`
- `components/libkoiki/src/libkoiki/repositories/`
- `components/libkoiki/src/libkoiki/services/`
- `components/libkoiki/src/libkoiki/events/`
- `components/libkoiki/src/libkoiki/tasks/`

## Role of libkoiki

`components/libkoiki/` is the shared backend framework layer.

It should contain:

- reusable API behavior
- shared authentication and authorization behavior
- configuration and infrastructure concerns
- shared persistence and schema patterns
- common service and repository patterns
- cross-cutting concerns such as logging, monitoring, middleware, and transactions

It should not become a container for business-specific rules.

## Placement Rules

A change belongs in `components/libkoiki/` when it is:

- reusable across multiple applications
- part of the framework contract
- independent of this project's specific business workflow
- better expressed as a shared service, schema, repository, or core utility

If reusability is unclear, prefer keeping the change out of `components/libkoiki/` until the abstraction is justified.

## Working Rules

When implementing a shared framework change:

1. confirm the behavior is truly reusable
2. find the nearest existing pattern in the same layer
3. extend current interfaces before adding new abstractions
4. keep cross-cutting concerns in their existing shared modules
5. check whether the application layer must be updated to consume the change

## Layer Expectations

Prefer the existing layered split.

- endpoints handle request wiring and validation
- services hold use-case logic
- repositories hold persistence logic
- models and schemas define shared data contracts
- core modules hold cross-cutting infrastructure behavior

Do not put non-trivial business logic directly into endpoint or repository code when the service layer should own it.

## Compatibility Rules

Changes in `components/libkoiki/` may affect `components/koiki_ref_app/`, compatibility wrappers, and tests indirectly.

Before finishing a framework change, check:

- whether application code composes the changed interface
- whether existing DI patterns still fit
- whether current tests still reflect the intended contract
- whether framework changes introduce assumptions specific to the current project

## Guardrails

Avoid:

- introducing project-specific business rules into shared code
- creating new base abstractions before confirming existing patterns are insufficient
- duplicating functionality already owned by another framework module
- forcing `components/koiki_ref_app/` to work around a shared change with unnecessary duplication

## Validation Standard

Validate framework changes at the scope that matches their impact.

This often includes:

- unit tests for local shared behavior
- integration tests when DB, auth, middleware, or DI wiring is affected
- application-level verification when `components/koiki_ref_app/` composes the changed framework behavior
