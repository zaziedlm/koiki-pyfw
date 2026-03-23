# app

## Purpose

This document defines how to work in `app/`, the application-specific backend layer built on top of `libkoiki/`.

Use this document when implementing business features, project-specific integrations, or application-level composition of shared framework capabilities.

## Scope

Typical areas include:

- `app/main.py`
- `app/api/v1/`
- `app/services/`
- `app/repositories/`
- `app/models/`
- `app/schemas/`
- `app/core/`

## Role of app

`app/` is where project-specific backend behavior lives.

It should contain:

- business-specific API behavior
- application-specific services and repositories
- domain-specific models and schemas when needed
- project-specific SSO and SAML integration
- application-level composition of shared `libkoiki/` capabilities

It should not duplicate framework behavior that already belongs in `libkoiki/`.

## Placement Rules

A change belongs in `app/` when it is:

- tied to the current business domain or workflow
- specific to this application's integrations
- an application-level use of shared framework functionality
- not broadly reusable across multiple applications

If a feature can be implemented by composing existing `libkoiki/` behavior, prefer that over adding new framework changes.

## Working Rules

When implementing an application change:

1. confirm the behavior is project-specific
2. reuse existing `libkoiki/` capabilities first
3. add only the layers needed for the feature
4. keep application wiring in current router and service patterns
5. check whether config, migrations, or frontend contracts must change too

## Current Structure

In the current repository:

- application routes are organized under `app/api/v1/`
- application composition is centered in `app/main.py`
- business services and repositories live under `app/services/` and `app/repositories/`
- project-specific auth integrations such as SSO and SAML live in `app/`

Prefer extending this structure instead of reviving older patterns from historical design documents.

## Relationship to libkoiki

`app/` should compose `libkoiki/`, not compete with it.

- use framework services, schemas, and auth behavior where appropriate
- keep business decisions in the application layer
- only push code down into `libkoiki/` when it becomes clearly reusable

## Guardrails

Avoid:

- reimplementing shared framework behavior inside `app/`
- pushing business-specific assumptions into `libkoiki/`
- creating parallel patterns when a nearby app module already defines the convention
- adding unnecessary layers for a small feature

## Validation Standard

Validate application changes primarily at the application level.

This often includes:

- app-focused unit tests for business logic
- integration tests for route, DB, auth, or DI behavior
- cross-checks against framework contracts when `libkoiki/` behavior is composed
