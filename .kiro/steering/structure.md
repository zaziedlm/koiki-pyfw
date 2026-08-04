# Project Structure

## Core Principle

**Layered separation**: Framework layer (`components/libkoiki/`) provides reusable capabilities; application layer (`components/koiki_ref_app/`) builds business logic on top.

## Top-Level Directories

```
koiki-v07/
├── components/              # Core implementation workspace
│   ├── libkoiki/           # Reusable framework layer
│   └── koiki_ref_app/      # Reference application layer
├── app/                    # Compatibility wrapper (legacy imports only, no new code)
├── apps/                   # Downstream business applications (reserved)
├── frontend/               # Reference Vite + React SPA
├── tests/                  # Root-level shared, e2e, and agent guidance tests
├── docs/                   # Design documentation and agent guidance
├── openspec/               # OpenSpec capability specs and change proposals
├── .aidx/                  # AI-driven development operations (spec ledger, feedback loops)
├── .kiro/                  # Kiro IDE configuration (steering, skills, hooks)
├── ops/                    # Operations scripts, security testing
├── docker/                 # Docker configurations (Keycloak realm exports)
└── pyproject.toml          # Workspace root package definition
```

## Backend Structure

### `components/libkoiki/` (Framework Layer)

```
libkoiki/
├── src/libkoiki/
│   ├── api/v1/             # Framework API routes (auth, users, roles, permissions, todos)
│   ├── core/               # Config, security, logging, dependencies, middleware
│   ├── models/             # SQLAlchemy models (User, Role, Permission, etc.)
│   ├── repositories/       # Data access layer (async repositories)
│   ├── schemas/            # Pydantic schemas (request/response DTOs)
│   ├── services/           # Business logic layer (auth, user, role, permission services)
│   ├── auth/               # Authentication implementations (JWT, SSO/OIDC, SAML)
│   └── utils/              # Shared utilities
├── tests/                  # Framework-owned tests
└── pyproject.toml          # Framework package definition
```

**Owns**: Reusable auth mechanisms, RBAC infrastructure, base API patterns, shared models/schemas/services, framework extension points.

### `components/koiki_ref_app/` (Application Layer)

```
koiki_ref_app/
├── src/koiki_ref_app/
│   ├── api/v1/             # Application-specific API routes
│   ├── models/             # Application-specific models
│   ├── repositories/       # Application-specific repositories
│   ├── schemas/            # Application-specific schemas
│   ├── services/           # Application-specific business logic
│   ├── asgi.py             # ASGI application entrypoint
│   └── app_factory.py      # Application factory and composition
├── alembic/                # Database migrations (application-owned)
│   ├── versions/           # Migration scripts
│   └── env.py              # Alembic environment config
├── tests/                  # Application-owned tests
└── pyproject.toml          # Application package definition
```

**Owns**: Business workflows, application composition, SSO/SAML wiring for this project, domain-specific features, migration management.

### `app/` (Compatibility Wrapper)

Minimal wrapper maintaining `app.main:app` import path for legacy compatibility. **Do not add new implementation here.**

## Frontend Structure

```
frontend/
├── src/
│   ├── components/         # React components (ui/, features/, layout/)
│   ├── features/           # Feature-specific logic (auth/, todos/, profile/)
│   ├── lib/                # Utilities, API client, types
│   ├── hooks/              # Custom React hooks
│   ├── stores/             # Zustand stores
│   └── main.tsx            # Application entry point
├── public/                 # Static assets
├── tests/                  # Frontend tests
└── package.json            # Frontend dependencies
```

## Testing Structure

```
tests/                      # Root-level tests
├── unit/
│   └── agent_guidance/     # Agent guidance validation tests
├── integration/
│   └── services/           # Cross-layer integration tests
└── conftest.py             # Shared test fixtures

components/libkoiki/tests/  # Framework layer tests
components/koiki_ref_app/tests/  # Application layer tests
```

**Test placement rule**: Place tests near the responsibility they validate. Framework tests in `libkoiki/tests/`, application tests in `koiki_ref_app/tests/`, cross-layer tests in root `tests/`.

## Documentation Structure

```
docs/
├── agent/                  # Agent operational guidance (read first)
│   ├── boundaries.md       # Layer separation rules
│   ├── architecture.md     # Layered architecture patterns
│   ├── environment.md      # Development environment setup
│   ├── testing.md          # Testing strategy
│   └── auth-security.md    # Authentication/security guidance
├── design_kkfw_0.8.0.md    # Current version design overview
├── dev/                    # Development task records
└── frontend-spa-implementation-guide.ja.md  # Frontend contract guide
```

## OpenSpec Structure

```
openspec/
├── specs/                  # Capability specifications (source of truth for intended behavior)
├── changes/                # Change proposals and work-in-progress specs
└── package.json            # OpenSpec CLI tooling
```

## AI Development Framework

```
.aidx/
├── loop-design/            # Spec ledger and feedback loops
│   ├── SPEC-MAP.md         # High-level spec dependency map
│   └── [capability]/       # Per-capability feedback loop records
└── SPEC-CHEATSHEET.md      # Quick reference for spec operations

.kiro/
├── steering/               # Always-included agent context (this file, product.md, tech.md)
├── skills/                 # Task-specific agent skills
└── hooks/                  # Agent automation hooks
```

## Layer Communication Rules

### Dependency Flow (One Direction)

```
API Layer → Service Layer → Repository Layer → Model Layer
     ↓            ↓                ↓              ↓
All layers can use: Core/Infrastructure (config, auth, logging, etc.)
```

**Never reverse this flow.** Lower layers must not depend on higher layers.

### Cross-Layer Boundaries

- **libkoiki → koiki_ref_app**: Application imports and extends framework. Framework must not import application code.
- **Frontend → Backend**: Frontend consumes backend APIs. Backend does not depend on frontend code.
- **Test → Implementation**: Tests import implementation code. Implementation must not import tests.

## File Placement Decision Tree

1. **Is it reusable across multiple applications?**
   - Yes → `components/libkoiki/`
   - No → Continue to 2

2. **Is it business-specific to this reference application?**
   - Yes → `components/koiki_ref_app/`
   - No → Continue to 3

3. **Is it downstream customer/tenant-specific?**
   - Yes → `apps/[customer]/`
   - No → Reconsider if it belongs in libkoiki

4. **Is it frontend code?**
   - Yes → `frontend/`

5. **Is it documentation?**
   - Yes → `docs/` (architecture, design) or `.aidx/` (spec ledger)

## Anti-Patterns to Avoid

- Adding business logic to `components/libkoiki/` for convenience
- Adding new code to `app/` (compatibility wrapper only)
- Creating parallel structure instead of extending existing patterns
- Bypassing service layer for non-trivial business logic
- Duplicating framework behavior in application layer
- Introducing new directory conventions without strong justification
