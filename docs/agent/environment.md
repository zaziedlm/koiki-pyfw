# Agent Environment

## Purpose

This document records environment issues that can affect AI-agent validation in this repository.

Read this before running commands that import application settings, execute tests, or sync dependencies.

## Application Environment Variables

Treat repository application settings as the source of truth.

- `DEBUG` in KOIKI-FW is a boolean application setting.
- Valid project values are boolean forms such as `True`, `False`, `true`, and `false`.
- Do not reinterpret non-boolean values as application settings unless the project explicitly defines them.

## Codex DEBUG Collision

Codex sessions may inherit `DEBUG=release` in the process environment.

This value is not defined by this repository and is not a KOIKI-FW application setting. It appears to come from the agent execution environment or its parent process, where `DEBUG=release` has a different meaning from `Settings.DEBUG: bool`.

When this inherited value reaches `libkoiki.core.config.Settings`, Pydantic correctly treats it as invalid for a boolean field.

For Codex validation only:

- explicitly set `DEBUG=True` or `DEBUG=False` when running commands that import application settings
- do not change application code to accept `release` as a boolean debug value
- do not document `DEBUG=release` as a supported project configuration

For normal local development:

- use the repository `.env` files or explicit boolean environment values
- run commands such as `uv sync` and `uv run ...` normally

## uv Cache in Sandboxed Agents

Codex sandboxed commands may be unable to access the user's default uv cache under `AppData\Local\uv\cache`.

This is an agent sandbox permission issue, not a project dependency-management requirement.

For Codex validation only, if the default cache is blocked:

- rerun the same command with the required approval when appropriate
- use a workspace-local `UV_CACHE_DIR` only as a temporary agent workaround
- do not make `UV_CACHE_DIR=.uv-cache-codex` part of the normal developer workflow

For normal local development, `uv sync` should be sufficient unless the local machine has an independent uv cache problem.
