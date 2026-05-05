# Boundaries

## Purpose

This project separates reusable framework capabilities from application-specific business implementation.

- `components/libkoiki/` contains shared framework behavior.
- `components/koiki_ref_app/` contains reference application behavior built on top of `components/libkoiki/`.
- root `app/` is a compatibility wrapper for legacy imports and entrypoints.

Preserve this separation unless there is a clear architectural reason to change it.

## Placement Rules

Place code in `components/libkoiki/` when it is:

- reusable across multiple applications or domains
- part of shared API, auth, config, middleware, persistence, or schema infrastructure
- a framework-level extension point or common service
- not coupled to this project's business rules

Place code in `components/koiki_ref_app/` when it is:

- business-specific or tenant-specific
- specific to current workflows, domain rules, or integrations
- an application-level composition of existing framework capabilities
- tied to current SSO, SAML, or business feature behavior for this project

## API Ownership

Framework APIs in `components/libkoiki/` must be reusable framework capabilities or explicitly documented starter/sample capabilities.

Application APIs in `components/koiki_ref_app/` should own project-specific workflows, integrations, and UI-facing application behavior.

Downstream or customer-specific APIs should start under `apps/` unless they are clearly reusable framework behavior or reference-app starter behavior.

The current Todo API is treated as a `libkoiki` starter/sample capability. Do not use it as precedent for putting new business-specific APIs into `components/libkoiki/`.

## Decision Heuristic

When deciding where a change belongs, ask:

1. Would another application built on KOIKI-FW likely need this?
2. Is this a framework capability or a business rule?
3. Would moving this into `components/libkoiki/` introduce project-specific assumptions?
4. Can the application solve this by composing existing framework behavior instead?

If the answer is unclear, prefer keeping the change in `components/koiki_ref_app/` first.

## Cross-Boundary Changes

Some changes legitimately span both layers.

Typical examples:

- adding a reusable framework capability in `components/libkoiki/`
- wiring that capability into current reference application flows in `components/koiki_ref_app/`
- updating tests in both framework and application scopes

In these cases:

- keep shared behavior in `components/libkoiki/`
- keep business decisions in `components/koiki_ref_app/`
- do not duplicate the same logic in both places

## Anti-Patterns

Avoid these patterns:

- moving business rules into `components/libkoiki/` for convenience
- reimplementing shared framework behavior inside `components/koiki_ref_app/`
- introducing a new abstraction layer before confirming existing patterns are insufficient
- treating historical documentation as more authoritative than current code

## Source of Truth

When documentation and implementation differ:

1. current implementation wins
2. boundary rules in shared agent docs come next
3. historical design documents are reference material, not operational truth
