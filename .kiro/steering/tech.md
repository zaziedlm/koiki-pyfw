# Tech Stack

## Backend

- **Language**: Python >=3.11.7, <4.0
- **Framework**: FastAPI >=0.136.3 with Starlette >=1.1.0
- **ASGI Server**: Uvicorn >=0.34.3
- **Database**: PostgreSQL 15 with async SQLAlchemy 2.0.23+
- **Database Driver**: asyncpg (async), psycopg2-binary (sync/migrations)
- **Migrations**: Alembic >=1.16.2
- **Validation**: Pydantic >=2.11.7, pydantic-settings >=2.10.0
- **Authentication**: PyJWT[crypto] >=2.12.0, bcrypt >=4.3.0
- **SAML**: python3-saml >=1.16.0, xmlsec >=1.3.13
- **Logging**: structlog >=25.4.0
- **HTTP Client**: httpx >=0.28.1
- **Caching**: Redis >=6.2.0 (optional, configurable)
- **Rate Limiting**: slowapi >=0.1.8, limits >=5.4.0
- **Package Manager**: uv (workspace mode)

## Frontend

- **Language**: TypeScript 5
- **Framework**: React 19
- **Build Tool**: Vite 7
- **Routing**: react-router 7
- **State Management**: Zustand 5, TanStack Query 5
- **Forms**: react-hook-form 7 + Zod 4
- **UI Components**: Radix UI primitives
- **Styling**: Tailwind CSS 4
- **Testing**: Vitest 4, Testing Library, MSW 2
- **Linting**: ESLint 9, Prettier 3

## Infrastructure

- **Containerization**: Docker, Docker Compose
- **Database**: PostgreSQL 15 container
- **Identity Provider**: Keycloak 26.3.5 (dev/test)
- **CI/CD**: GitHub Actions

## Common Commands

### Backend Development

```bash
# Install dependencies (from project root)
uv sync

# Run tests with coverage
uv run pytest --cov=koiki_ref_app --cov=libkoiki --cov-report=term-missing \
  components/libkoiki/tests/ \
  components/koiki_ref_app/tests/ \
  tests/unit/agent_guidance/ \
  tests/integration/services/

# Run specific test markers
uv run pytest -m unit                # Fast unit tests only
uv run pytest -m integration         # Integration tests
uv run pytest -m db_integration      # PostgreSQL integration (requires RUN_DB_INTEGRATION=1)

# Database migrations (from project root, with running db service)
cd components/koiki_ref_app
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
cd ../..

# Security audit
uv run pip-audit
uv run bandit -r components/libkoiki/src components/koiki_ref_app/src
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Development server
npm run dev              # Runs on http://localhost:3000

# Type checking
npm run check-types

# Linting
npm run lint

# Testing
npm test                 # Run tests once
npm run test:watch       # Watch mode

# Production build
npm run build
npm run preview          # Preview production build
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Start with build
docker-compose up --build -d

# View logs
docker-compose logs -f app          # Backend logs
docker-compose logs -f frontend     # Frontend logs
docker-compose logs -f db           # Database logs
docker-compose logs -f keycloak     # Keycloak logs

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose up --build -d app
```

### Security Testing

```bash
# From project root - comprehensive security test
./ops/scripts/run_tests.sh test

# From ops directory - granular control
cd ops
bash scripts/security_test_manager.sh test
```

## Service Ports

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Keycloak: http://localhost:8090
- Keycloak Management: localhost:9000

## Environment Configuration

- Backend environment: `.env` (see `.env.example`)
- Frontend environment: `frontend/.env.docker` for Docker builds
- All services configured via Docker Compose environment variables
