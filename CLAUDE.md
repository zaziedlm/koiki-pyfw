# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Security Update History

### 2025-06-21: Critical Security Vulnerabilities Fixed + Comprehensive Dependency Modernization
**Security Priority Update**: All known vulnerabilities resolved + Complete dependency stack modernization

**Fixed Vulnerabilities:**
- **fastapi**: 0.104.1 → 0.115.13 (Fixed: PYSEC-2024-38)
- **python-jose**: 3.3.0 → 3.5.0 (Fixed: PYSEC-2024-232, PYSEC-2024-233)
- **starlette**: 0.27.0 → 0.46.2 (Fixed: GHSA-f96h-pmfr-66vw)

**Python 3.13 Compatibility:**
- **asyncpg**: 0.29.0 → 0.30.0 (Python 3.13 compilation support)
- **pydantic**: 2.9.2 → 2.11.7 (Enterprise requirement: pydantic >=2.7.0)

**Phase 1 Updates (Low Risk):**
- **email-validator**: 2.1.2 → 2.2.0 (Validation improvements)
- **pytest-cov**: 6.1.1 → 6.2.1 (Test coverage enhancements)

**Phase 2 Updates (Medium Risk):**
- **httpx**: 0.25.2 → 0.28.1 (HTTP client improvements)
- **structlog**: 23.2.0 → 25.4.0 (Structured logging enhancements)
- **alembic**: 1.12.1 → 1.16.2 (Database migration improvements)
- **anyio**: 3.7.1 → 4.9.0 (Async I/O performance)
- **limits**: 5.3.0 → 5.4.0 (Rate limiting improvements)

**Phase 3 Updates (High Risk):**
- **uvicorn**: 0.24.0 → 0.34.3 (ASGI server major performance improvements)
- **pytest**: 7.4.4 → 8.4.1 (Test framework major upgrade)
- **pytest-asyncio**: 0.23.8 → 1.0.0 (Async testing major upgrade)
- **redis**: 5.0.8 → 6.2.0 (Redis client major upgrade)
- **prometheus-fastapi-instrumentator**: 5.7.1 → 7.1.0 (Monitoring enhancements)

**Container Deployment Verification:**
- ✅ **Build**: 51 packages successfully installed
- ✅ **Performance**: Response time 0.055-0.080s (excellent)
- ✅ **API Tests**: Full CRUD operations, authentication, security headers
- ✅ **Database**: PostgreSQL connection, Alembic migrations functional

**Security Audit Result:** ✅ No known vulnerabilities found

**Security Tools Configuration:**
- ✅ **pip-audit**: 2.9.0 (OSV database vulnerability scanning)
- ✅ **bandit**: 1.8.5 (Static security analysis)
- ❌ **safety**: Excluded (pydantic <2.0 dependency conflict)

**Enterprise Security Strategy:**
- Priority: Security fixes over version stability during development phase
- Approach: Proactive updates when impact scope and dependency count allow
- Philosophy: Leverage development period for comprehensive modernization
- Result: Production-ready modernized dependency stack with zero known vulnerabilities

## Poetry 2.x Migration Summary

This project has been fully optimized for Poetry 2.x with PEP 621 compliance, providing:
- **Enhanced Performance**: Parallel dependency installation with optimized caching
- **Modern Standards**: Full PEP 621 compliance for improved tool interoperability  
- **Organized Dependencies**: Clear separation of main, dev, and test dependencies
- **Optimized Workflows**: Streamlined CI/CD with Poetry 2.x features
- **Future-Proof Architecture**: Ready for Python packaging ecosystem evolution

## Development Commands (Poetry 2.x Optimized)

### Environment Setup
```bash
# Poetry 2.x: Initial performance configuration
poetry config installer.parallel true
poetry config installer.max-workers 10
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# Poetry 2.x: Dependency verification and installation
poetry check --lock
poetry install

# Poetry 2.x: Use dependency groups for targeted installation
poetry install --with dev          # Install with development dependencies
poetry install --with test         # Install with test dependencies  
poetry install --with dev,test      # Install with multiple groups
poetry install --only=main         # Install only production dependencies
poetry install --only=dev          # Install only development dependencies

# For export functionality (if needed)
poetry self add poetry-plugin-export

# Run with Docker Compose (recommended for development)
docker-compose up --build

# Run locally (requires PostgreSQL setup)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Activate environment
poetry shell
```

### Testing
```bash
# Poetry 2.x: Install test dependencies first
poetry install --with test

# Run all tests
poetry run pytest

# Run specific test files
poetry run pytest tests/unit/test_hello.py
poetry run pytest tests/integration/app/api/test_todos_api.py

# Run tests with coverage
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing --cov-report=html tests/

# Poetry 2.x: Run tests for specific dependency groups
poetry install --only=test
poetry run pytest
```

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current
```

### Code Quality & Enterprise Dependency Management
```bash
# Poetry 2.x with PEP 621 compliance for enterprise dependency management
# Project follows strict enterprise versioning: minor version locks for stability

# Poetry 2.x: Comprehensive dependency verification
poetry check --lock                 # Verify lock file consistency
poetry lock                        # Update lock file if needed

# Poetry 2.x: Dependency synchronization and management
poetry sync                        # Sync environment with lock file
poetry install --sync              # Alternative sync method

# Install specific dependency groups (Poetry 2.x feature)
poetry install --only=main         # Production dependencies only
poetry install --only=dev          # Development dependencies only
poetry install --only=test         # Test dependencies only
poetry install --only=security     # Security audit tools
poetry install --with dev,test,security  # Multiple groups

# Enterprise Security Auditing (Python 3.13 Compatible)
# Note: safety excluded due to pydantic <2.0 dependency conflict
poetry install --with security     # Install security tools
poetry run pip-audit               # OSV database vulnerability scan (pydantic independent)
poetry run pip-audit --format=json --output=security-audit.json  # JSON report
poetry run bandit -r . --severity-level medium  # Static security analysis
poetry run bandit -r . -f json -o security-bandit.json  # JSON report

# Environment and dependency information
poetry env info                     # Environment details
poetry show --tree                  # Dependency tree
poetry show --tree --only=main     # Production dependency tree
poetry show --outdated             # Check for updates
poetry config --list               # Current Poetry configuration

# Cache management (Poetry 2.x optimization)
poetry cache clear --all pypi       # Clear package cache
poetry cache list                   # List cached packages
```

## Architecture Overview

This is KOIKI-FW v0.5.0, an enterprise-grade FastAPI application framework optimized for Poetry 2.x and PEP 621 compliance with the following key characteristics:

### Project Structure
- **Root `/`**: Main application entry point and Docker configuration
- **`app/`**: Application-specific code (endpoints, models, schemas, services, repositories)
- **`libkoiki/`**: Reusable framework library containing core functionality
- **`alembic/`**: Database migrations
- **`tests/`**: Unit and integration tests
- **`docs/`**: Project documentation

### Framework Architecture (libkoiki)
The libkoiki library provides enterprise-ready components:

- **`core/`**: Configuration, logging, security, middleware, error handling
- **`api/v1/`**: API endpoints (auth, users, todos) and routing
- **`db/`**: Database session management and base models
- **`models/`**: SQLAlchemy ORM models (User, Todo, Role, Permission)
- **`repositories/`**: Data access layer following repository pattern
- **`services/`**: Business logic layer
- **`schemas/`**: Pydantic models for API serialization
- **`events/`**: Event publishing and handling system
- **`tasks/`**: Celery task definitions (commented out in current version)
- **`utils/`**: Utility functions

### Application Layer (`app/`)
Application-specific implementations that extend the framework:
- Uses libkoiki as a local development dependency (Poetry 2.x: `libkoiki = {path = "libkoiki", develop = true}`)
- Follows PEP 621 standard in pyproject.toml for metadata and dependencies
- Follows the same layered architecture pattern

### Key Technologies
- **FastAPI**: Web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL
- **Alembic**: Database migrations
- **Pydantic**: Data validation and serialization
- **structlog**: Structured logging
- **JWT**: Authentication via python-jose
- **slowapi**: Rate limiting
- **Redis**: Optional for event publishing and enhanced rate limiting
- **Docker**: Containerization with multi-stage builds

### Configuration System
Settings are managed through `libkoiki.core.config.Settings` using pydantic-settings:
- Environment variables override defaults
- Separate configurations for development/testing/production
- Database URL, Redis settings, CORS origins, rate limiting, etc.
- Poetry 2.x: Dependencies managed via PEP 621 [project] section
- Development dependencies organized in Poetry 2.x dependency groups

### Development Patterns

#### Dependency Injection
The framework uses FastAPI's dependency injection system extensively:
- Database sessions injected via `get_db()`
- Authentication via `get_current_user()`
- Rate limiting via slowapi decorators

#### Repository Pattern
Data access follows repository pattern:
- Base repository in `libkoiki.repositories.base`
- Specific repositories extend base functionality
- Services layer calls repositories, not models directly

#### Event System
Async event handling system (Redis-based, currently disabled):
- Event publishers in services
- Event handlers for cross-cutting concerns
- Supports distributed event processing

### Redis Integration
Redis support is optional and gracefully degrades:
- If Redis unavailable, uses in-memory alternatives
- Event system becomes no-op
- Rate limiting falls back to fixed-window strategy

### Security Features
- JWT-based authentication with role-based access control (RBAC)
- Security headers middleware
- Rate limiting per endpoint
- Audit logging middleware
- Password hashing with bcrypt

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

## Development Notes

### Database
- Uses PostgreSQL exclusively (no SQLite support)
- Async SQLAlchemy 2.0 with asyncpg driver
- Connection pooling configured in settings
- All schema changes via Alembic migrations

### Testing Strategy
- Separate unit and integration test directories
- Test configuration in `pytest.ini_options` (pyproject.toml)
- Coverage tracking for `app` and `libkoiki` modules
- Test database setup via conftest.py

### Docker Development
- Multi-stage Dockerfile optimized for Poetry 2.x with parallel installation
- Poetry 2.x performance optimizations: parallel workers, cache management
- Non-root user (appuser) for security
- Health checks configured
- Volume mounts for live reload during development
- Optimized layer caching for Poetry dependencies

### Poetry 2.x & PEP 621 Features
- **PEP 621 Compliance**: Project metadata and dependencies in standardized `[project]` section
- **Dependency Groups**: Organized development, test, and production dependencies
- **Performance Optimization**: Parallel installation with configurable worker count
- **Modern Build System**: poetry-core>=1.5.0 for enhanced Poetry 2.x features
- **Standardized Dependencies**: Semantic versioning ranges instead of wildcards
- **Tool Interoperability**: PEP 621 compliance enables easy migration between build tools

### Environment Configuration
- `.env` file for local settings (not committed)
- Settings cascade: environment variables → .env → defaults
- Separate configurations per environment (APP_ENV setting)
- Poetry 2.x: Optimized virtualenv and cache configuration

## Enterprise Security Strategy

### Security-First Dependency Management

**Core Principles:**
1. **Security Over Stability**: During development phase, prioritize security fixes over version stability
2. **Proactive Updates**: Leverage development periods for comprehensive security modernization
3. **Impact-Based Decisions**: Update scope determined by impact analysis and dependency count
4. **Compatibility Priority**: Maintain enterprise requirements (e.g., pydantic >=2.7.0)

**Vulnerability Response Framework:**

```bash
# 1. Immediate Assessment
poetry run pip-audit --format=json --output=vuln-assessment.json
poetry run pip-audit  # Human-readable summary

# 2. Impact Analysis
poetry show --tree | grep -E "(vulnerable_package|dependency_chain)"
poetry show vulnerable_package  # Check version and dependents

# 3. Security-Priority Update Process
# Update to security-fixed version (not just minimum required)
poetry add "fastapi>=0.115.13,<0.116.0"  # Latest stable with security fixes
poetry add "python-jose>=3.4.0,<3.6.0"   # Beyond minimum fix version

# 4. Verification
poetry lock
poetry install
poetry run pip-audit  # Confirm no vulnerabilities

# 5. Compatibility Testing
poetry run pytest  # Ensure functionality maintained
```

**Development Phase Security Strategy:**
- **Proactive Approach**: Update during development when changes are easier to implement
- **Comprehensive Scope**: Address not just immediate fixes but also modernization opportunities
- **Enterprise Requirements**: Maintain compatibility with enterprise-grade dependencies
- **Testing Priority**: Ensure all updates maintain system functionality

**Tool Selection Rationale:**
- **pip-audit**: Primary tool (pydantic-independent, OSV database)
- **bandit**: Static analysis (pydantic-independent)
- **safety**: Excluded due to pydantic <2.0 dependency conflict
- **Alternative**: Use pip-audit which provides equivalent vulnerability detection

### Security Audit Integration

**Daily Security Monitoring:**
```bash
# Automated security check script
#!/bin/bash
echo "=== Daily Security Audit ==="
poetry run pip-audit --format=json --output="audit-$(date +%Y%m%d).json"
poetry run pip-audit
poetry run bandit -r . --severity-level medium
poetry show --outdated | grep -E "(critical|security)"
```

**Pre-Deployment Security Gate:**
```bash
# Security gate for deployment pipeline
poetry install --with security
poetry run pip-audit || exit 1  # Block deployment on vulnerabilities
poetry run bandit -r . --severity-level high || exit 1  # Block on high-severity issues
```

## Poetry 2.x Troubleshooting

### Common Issues and Solutions

```bash
# If dependency installation fails
poetry cache clear --all pypi
poetry install --no-cache

# If lock file is out of sync
poetry check --lock
poetry lock
poetry install

# If local libkoiki package fails to install
cd libkoiki
poetry build
cd ..
poetry install

# Check Poetry and environment status
poetry --version
poetry env info
poetry config --list

# Reset Poetry environment if needed
poetry env remove python
poetry install
```

### Enterprise Security Issues

```bash
# Python 3.13 + pydantic >=2.7.0 Compatible Security Audit
poetry install --with security
poetry run pip-audit --format=json --output=audit-issues.json
poetry run pip-audit  # Human-readable output

# Emergency security update process (Enterprise-grade)
poetry add "package_name>=fixed.version,<next.major.0"  # Security fix with stability
poetry lock  # Update lock file
poetry install
poetry run pip-audit  # Verify no vulnerabilities remain

# Check for specific CVE
poetry run pip-audit | grep -i "CVE-XXXX-XXXX"
poetry show package_name  # Check installed version

# Python 3.13 Compatibility Issues Resolution
# If asyncpg compilation fails
poetry add "asyncpg>=0.30.0,<0.31.0"  # Python 3.13 compatible version
poetry lock
poetry install

# If pydantic dependency conflicts occur
poetry add "pydantic>=2.9.0,<2.12.0"  # Enterprise compatible range
poetry add "pydantic-settings>=2.9.1,<2.12.0"  # Matching pydantic-settings

# Generate comprehensive security compliance report
poetry run pip-audit --format=json --output=compliance-report.json
poetry run bandit -r . -f json -o security-static-analysis.json
echo "Security audit complete. Reports: compliance-report.json, security-static-analysis.json"

# Tool compatibility verification
poetry run python -c "import asyncpg, pydantic, fastapi; print('✅ Core dependencies compatible')"
poetry run pip-audit --version
poetry run bandit --version
```

### Python 3.13 Specific Troubleshooting

```bash
# Python 3.13 Compatibility Verification
python --version  # Ensure Python 3.13.x

# If C extension compilation fails (common with Python 3.13)
poetry config installer.parallel false  # Disable parallel for troubleshooting
poetry cache clear --all pypi
poetry install --no-cache

# asyncpg Python 3.13 Fix
poetry add "asyncpg>=0.30.0,<0.31.0"
poetry lock
poetry install

# pydantic 2.x Enterprise Requirements
poetry add "pydantic>=2.9.0,<2.12.0"  # Latest stable compatible with enterprise tools
poetry run python -c "import pydantic; print(f'pydantic {pydantic.__version__} ready')"

# Security tools compatibility check
poetry install --with security
poetry run pip-audit --version  # Should show 2.9.0+
poetry run bandit --version     # Should show 1.8.5+

# If wheel building fails
pip install --upgrade pip setuptools wheel
poetry install --no-cache
```

### Migration Notes
- **From Poetry 1.x**: All configurations have been updated to Poetry 2.x standards
- **PEP 621 Adoption**: Dependencies are now managed in `[project]` section
- **Dependency Groups**: Use `--with` and `--only` flags for targeted installations
- **Performance**: Parallel installation is enabled by default in CI/CD and Docker

### Key Configuration Files
- **`pyproject.toml`**: PEP 621 compliant project configuration with Poetry 2.x features
- **`libkoiki/pyproject.toml`**: Framework library configuration optimized for Poetry 2.x
- **`.github/workflows/ci.yml`**: CI/CD pipeline with Poetry 2.x optimizations
- **`Dockerfile`**: Container build optimized for Poetry 2.x parallel installation