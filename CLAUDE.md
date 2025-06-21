# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies with Poetry 2.x
poetry install

# For export functionality (if needed)
poetry self add poetry-plugin-export

# Run with Docker Compose (recommended for development)
docker-compose up --build

# Run locally (requires PostgreSQL setup)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Activate environment (Poetry 2.x recommended way)
poetry env activate
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run specific test files
poetry run pytest tests/unit/test_hello.py
poetry run pytest tests/integration/app/api/test_todos_api.py

# Run tests with coverage
poetry run pytest --cov=app --cov=libkoiki tests/
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

### Code Quality
```bash
# The project uses Poetry 2.x for dependency management
# No specific linting commands are configured yet - check pyproject.toml for updates

# Sync dependencies (Poetry 2.x feature - replaces poetry install --sync)
poetry sync

# Install dependencies without dev packages
poetry install --only=main
```

## Architecture Overview

This is KOIKI-FW v0.3.0, an enterprise-grade FastAPI application framework with the following key characteristics:

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
- Uses libkoiki as a dependency (`poetry.toml`: `libkoiki = {path = "libkoiki", develop = true}`)
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
- Multi-stage Dockerfile with Poetry 2.x
- Non-root user (appuser) for security
- Health checks configured
- Volume mounts for live reload during development

### Environment Configuration
- `.env` file for local settings (not committed)
- Settings cascade: environment variables → .env → defaults
- Separate configurations per environment (APP_ENV setting)