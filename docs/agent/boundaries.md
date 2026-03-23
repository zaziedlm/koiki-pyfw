# Boundaries

## Purpose

This project separates reusable framework capabilities from application-specific business implementation.

- `libkoiki/` contains shared framework behavior.
- `app/` contains business-specific behavior built on top of `libkoiki/`.

Preserve this separation unless there is a clear architectural reason to change it.

## Placement Rules

Place code in `libkoiki/` when it is:

- reusable across multiple applications or domains
- part of shared API, auth, config, middleware, persistence, or schema infrastructure
- a framework-level extension point or common service
- not coupled to this project's business rules

Place code in `app/` when it is:

- business-specific or tenant-specific
- specific to current workflows, domain rules, or integrations
- an application-level composition of existing framework capabilities
- tied to current SSO, SAML, or business feature behavior for this project

## Decision Heuristic

When deciding where a change belongs, ask:

1. Would another application built on KOIKI-FW likely need this?
2. Is this a framework capability or a business rule?
3. Would moving this into `libkoiki/` introduce project-specific assumptions?
4. Can the application solve this by composing existing framework behavior instead?

If the answer is unclear, prefer keeping the change in `app/` first.

## Cross-Boundary Changes

Some changes legitimately span both layers.

Typical examples:

- adding a reusable framework capability in `libkoiki/`
- wiring that capability into current business flows in `app/`
- updating tests in both framework and application scopes

In these cases:

- keep shared behavior in `libkoiki/`
- keep business decisions in `app/`
- do not duplicate the same logic in both places

## Anti-Patterns

Avoid these patterns:

- moving business rules into `libkoiki/` for convenience
- reimplementing shared framework behavior inside `app/`
- introducing a new abstraction layer before confirming existing patterns are insufficient
- treating historical documentation as more authoritative than current code

## Source of Truth

When documentation and implementation differ:

1. current implementation wins
2. boundary rules in shared agent docs come next
3. historical design documents are reference material, not operational truth
