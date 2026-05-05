# Reference App

## Purpose

This document defines how to work in `components/koiki_ref_app/`, the reference application backend layer built on top of `components/libkoiki/`.

Use this document when implementing business features, project-specific integrations, or application-level composition of shared framework capabilities.

## Scope

Typical areas include:

- `components/koiki_ref_app/src/koiki_ref_app/asgi.py`
- `components/koiki_ref_app/src/koiki_ref_app/main.py`
- `components/koiki_ref_app/src/koiki_ref_app/api/v1/`
- `components/koiki_ref_app/src/koiki_ref_app/services/`
- `components/koiki_ref_app/src/koiki_ref_app/repositories/`
- `components/koiki_ref_app/src/koiki_ref_app/models/`
- `components/koiki_ref_app/src/koiki_ref_app/schemas/`
- `components/koiki_ref_app/src/koiki_ref_app/core/`

## Role of koiki_ref_app

`components/koiki_ref_app/` is where reference application behavior lives.

It should contain:

- business-specific API behavior
- application-specific services and repositories
- domain-specific models and schemas when needed
- project-specific SSO and SAML integration
- application-level composition of shared `components/libkoiki/` capabilities

It should not duplicate framework behavior that already belongs in `components/libkoiki/`.

It should also not absorb downstream customer-specific API behavior unless that behavior is intended to become reference-app starter behavior. Downstream or customer-specific APIs should start under `apps/`.

## Placement Rules

A change belongs in `components/koiki_ref_app/` when it is:

- tied to the current business domain or workflow
- specific to this application's integrations
- an application-level use of shared framework functionality
- not broadly reusable across multiple applications

If a feature can be implemented by composing existing `components/libkoiki/` behavior, prefer that over adding new framework changes.

## Working Rules

When implementing an application change:

1. confirm the behavior is project-specific
2. reuse existing `components/libkoiki/` capabilities first
3. add only the layers needed for the feature
4. keep application wiring in current router and service patterns
5. check whether config, migrations, or frontend contracts must change too

## Current Structure

In the current repository:

- application routes are organized under `components/koiki_ref_app/src/koiki_ref_app/api/v1/`
- application composition is centered in `components/koiki_ref_app/src/koiki_ref_app/`
- business services and repositories live under `components/koiki_ref_app/src/koiki_ref_app/services/` and `components/koiki_ref_app/src/koiki_ref_app/repositories/`
- project-specific auth integrations such as SSO and SAML live in `components/koiki_ref_app/`
- root `app/` is a compatibility wrapper and should not receive new implementation by default

Prefer extending this structure instead of reviving older patterns from historical design documents.

## Relationship to libkoiki

`components/koiki_ref_app/` should compose `components/libkoiki/`, not compete with it.

- use framework services, schemas, and auth behavior where appropriate
- keep business decisions in the application layer
- only push code down into `components/libkoiki/` when it becomes clearly reusable

## Guardrails

Avoid:

- reimplementing shared framework behavior inside `components/koiki_ref_app/`
- pushing business-specific assumptions into `components/libkoiki/`
- treating the current `libkoiki` Todo sample as precedent for placing new business APIs in `components/libkoiki/`
- placing downstream customer-specific APIs in the reference app when they belong under `apps/`
- creating parallel patterns when a nearby app module already defines the convention
- adding unnecessary layers for a small feature

## Validation Standard

Validate application changes primarily at the application level.

This often includes:

- app-focused unit tests for business logic
- integration tests for route, DB, auth, or DI behavior
- cross-checks against framework contracts when `components/libkoiki/` behavior is composed
