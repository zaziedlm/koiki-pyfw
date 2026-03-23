# Auth and Security

## Purpose

This document defines the operational guidance for authentication, authorization, and security-sensitive changes in this repository.

Use this document when the task touches tokens, login flows, permissions, SSO, SAML, security monitoring, or security-related middleware and configuration.

## Scope

This guidance applies to changes in areas such as:

- `libkoiki/core/security.py`
- `libkoiki/core/security_config.py`
- `libkoiki/core/security_logger.py`
- `libkoiki/core/security_metrics.py`
- `libkoiki/core/middleware.py`
- `libkoiki/api/v1/endpoints/auth*.py`
- `libkoiki/api/v1/endpoints/security_monitor.py`
- `libkoiki/services/auth_service.py`
- `libkoiki/services/login_security_service.py`
- `libkoiki/services/password_reset_service.py`
- `app/services/sso_service.py`
- `app/services/saml_service.py`
- `app/api/v1/endpoints/sso_auth.py`
- `app/api/v1/endpoints/saml_auth.py`

## Security Boundary

Keep the security boundary explicit.

- shared auth, token, permission, password, audit, and rate-limiting behavior belongs in `libkoiki/`
- application-specific SSO, SAML, and business-auth integration belongs in `app/`
- do not move business-specific identity rules into shared framework code unless they are truly reusable

## Working Rules

When changing auth or security behavior:

1. trace the full request flow before editing
2. identify which checks happen in framework code and which happen in application code
3. preserve failure behavior unless there is an explicit reason to change it
4. update validation, logging, and tests together
5. review for privilege, token, redirect, session, and replay risks

## Authorization Rules

Authorization must not depend only on UI behavior.

- backend permission checks remain mandatory
- endpoint-level access rules must stay explicit
- role and permission checks must remain enforceable independently of frontend state

## SSO and SAML Rules

SSO and SAML are application-facing integrations and should usually remain in `app/`.

When working in this area:

- keep protocol and provider-specific behavior out of shared framework code unless a true shared abstraction is needed
- preserve redirect, assertion, metadata, and certificate handling carefully
- treat callback, token, and session transitions as security-sensitive paths
- validate both success and failure flows

## Guardrails

Avoid:

- weakening validation, audit, or rate-limit behavior without a clear reason
- changing auth logic in one layer when the flow spans multiple layers
- assuming a frontend redirect or hidden control is sufficient protection
- mixing framework token logic with project-specific identity assumptions

## Validation Standard

For auth and security-sensitive changes, use more than one validation angle when appropriate.

Prefer a mix of:

- focused unit tests for local logic
- integration coverage for request, permission, redirect, token, or session behavior
- manual review of edge cases where protocol or security behavior is hard to simulate fully

## Source Priority

When security guidance conflicts:

1. current implementation
2. shared agent docs
3. historical design references
