# AGENTS.md

## Purpose

This file is a short entry point for agents working in this repository.

The primary shared guidance lives under `docs/agent/`.

## Start Here

Read these files first:

1. `docs/agent/boundaries.md`
2. `docs/agent/architecture.md`
3. `docs/agent/testing.md`

Read these when relevant:

- `docs/agent/auth-security.md`
- `docs/agent/libkoiki.md`
- `docs/agent/app.md`

## Core Rules

- Keep reusable framework behavior in `libkoiki/`.
- Keep business-specific behavior in `app/`.
- Prefer current implementation over historical design notes when they conflict.
- Follow the existing layered structure unless there is a strong reason not to.
- Validate changes at the smallest scope that proves the behavior.

## Directory Intent

- `libkoiki/`: shared backend framework
- `app/`: current application-specific backend code
- `frontend/`: frontend code
- `tests/`: unit and integration validation

## Notes

Use this file as an entry point, not as a full rule reference.
Detailed guidance should remain in `docs/agent/`.
