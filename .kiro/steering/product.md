# Product: KOIKI-FW

KOIKI-FW is a FastAPI-based enterprise application framework for building secure, scalable web applications with modern authentication and authorization capabilities.

## Core Purpose

- Reusable framework for enterprise web applications
- Separation of framework layer (`components/libkoiki/`) from business application layer (`components/koiki_ref_app/`)
- Production-ready authentication (JWT, SSO/OIDC, SAML), RBAC, rate limiting, structured logging
- Reference implementation demonstrating framework usage patterns

## Key Capabilities

- **Authentication**: JWT tokens, refresh tokens, password reset, login attempt limiting, SSO/OIDC (Keycloak), SAML 2.0
- **Authorization**: Role-based access control (RBAC) with granular permissions
- **Security**: CSRF protection, rate limiting, audit logging, session management
- **Data Access**: Async SQLAlchemy, repository pattern, migration support (Alembic)
- **Monitoring**: Structured logging (structlog), Prometheus metrics support
- **Frontend Integration**: Cookie-based session authentication with CSRF protection, reference React SPA

## Target Users

- Enterprise application developers needing a secure, scalable FastAPI foundation
- Teams requiring OIDC/SAML integration
- Projects with complex authorization requirements

## Current Version

v0.8.0 - Frontend refreshed to Vite + React SPA with Cookie session authentication
