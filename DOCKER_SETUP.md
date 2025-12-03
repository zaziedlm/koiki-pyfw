# KOIKI Framework Docker Setup

This document describes the Docker containerization setup for the KOIKI Framework, including both the Python FastAPI backend and Next.js frontend.

## Overview

The Docker setup includes:
- **Backend**: FastAPI application with PostgreSQL database
- **Frontend**: Next.js application with TypeScript and Tailwind CSS
- **Database**: PostgreSQL 15 with persistent storage
- **Networking**: Internal Docker network for service communication
- **Unified stack**: `docker-compose.unified.yml` with profiles (dev / optimized / prod / prod-external) for consistent service naming and build targets

## Quick Start

### 1. Environment Setup

**Linux/macOS (Bash):**
```bash
# Copy environment templates
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local

# Edit configuration files as needed
nano .env
nano frontend/.env.local
```

**Windows (PowerShell):**
```powershell
# Copy environment templates
Copy-Item .env.example .env
Copy-Item frontend\.env.local.example frontend\.env.local

# Edit configuration files as needed
notepad .env
notepad frontend\.env.local
```

**Configuration Notes:**
- Backend configuration: `.env`
- Frontend local development: `frontend/.env.local`
- Common customizations:
  - `NEXT_PUBLIC_API_URL`: Change if backend runs on different port/host
  - `NEXT_PUBLIC_DEBUG`: Set to true for detailed logging
  - `NEXT_PUBLIC_DEFAULT_THEME`: Choose light, dark, or system
- Note: `.env.local` is for local non-Docker development
- Docker environments use `.env.docker` automatically

### 2. Start Services

```bash
# Production mode
./start-docker.sh up

# Production mode (external DB / external IdP)
docker compose -f docker-compose.production-external.yml up -d

# Development mode (with hot reload)
./start-docker.sh dev

# View logs
./start-docker.sh logs

# Unified stack (profiles: dev / optimized / prod / prod-external)
# env_file is chosen via ENV_FILE (.env for dev/optimized, .env.production for prod/prod-external)
ENV_FILE=.env docker compose -f docker-compose.unified.yml --profile dev up
ENV_FILE=.env docker compose -f docker-compose.unified.yml --profile optimized up -d
ENV_FILE=.env.production docker compose -f docker-compose.unified.yml --profile prod up -d
ENV_FILE=.env.production docker compose -f docker-compose.unified.yml --profile prod-external up -d
```

### 3. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

## Docker Compose Command Reference

### Basic Syntax

```bash
docker-compose [OPTIONS] [COMMAND] [ARGS...]
```

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `-f, --file FILE` | Specify compose file | `docker-compose -f docker-compose.unified.dev.yml up` |
| `-p, --project-name NAME` | Specify project name | `docker-compose -p myproject up` |
| `--env-file PATH` | Specify env file | `docker-compose --env-file .env.prod up` |

### Essential Commands

#### Start Services

```bash
# Start in foreground (see logs in terminal)
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Start with rebuild
docker-compose up --build

# Start specific services only
docker-compose up app db
```

**Windows PowerShell:**
```powershell
# Same commands work in PowerShell
docker-compose up -d --build
docker-compose -f docker-compose.unified.dev.yml up -d
```

#### Stop Services

```bash
# Stop services (keeps containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers, volumes, and images
docker-compose down -v --rmi all
```

#### View Logs

```bash
# View all logs
docker-compose logs

# Follow logs (live tail)
docker-compose logs -f

# View specific service logs
docker-compose logs app
docker-compose logs frontend

# Last 100 lines
docker-compose logs --tail=100 app
```

#### Build Images

```bash
# Build all services
docker-compose build

# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build app
```

#### Execute Commands in Containers

```bash
# Execute command in running container
docker-compose exec app bash

# Execute as root user
docker-compose exec -u root app bash

# Run one-off command
docker-compose run --rm app python --version
```

**Windows PowerShell:**
```powershell
# Same syntax
docker-compose exec app bash
docker-compose exec frontend sh
```

#### View Status

```bash
# List containers
docker-compose ps

# View images
docker-compose images

# View configuration
docker-compose config
```

### Advanced Usage

#### Multiple Compose Files

```bash
# Combine multiple files (later files override earlier)
docker-compose -f docker-compose.base.yml -f docker-compose.dev.yml up

# Production + overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

#### Scaling Services

```bash
# Scale specific service to N instances
docker-compose up -d --scale app=3

# Not recommended for services with published ports
```

#### Resource Management

```bash
# Remove stopped containers
docker-compose rm

# Remove unused volumes
docker volume prune

# System-wide cleanup
docker system prune -a
```

### Environment Variables

```bash
# Load from specific env file
docker-compose --env-file .env.dev up

# Override in command
POSTGRES_USER=admin docker-compose up
```

**Windows PowerShell:**
```powershell
# Set environment variable temporarily
$env:POSTGRES_USER="admin"
docker-compose up

# Or inline (requires CMD, not PowerShell core commands)
cmd /c "set POSTGRES_USER=admin && docker-compose up"
```

### Useful Command Combinations

```bash
# Restart services with rebuild
docker-compose down && docker-compose up -d --build

# View logs while starting
docker-compose up --build 2>&1 | tee build.log

# Check if services are healthy
docker-compose ps | grep healthy
```

**Windows PowerShell:**
```powershell
# Restart services with rebuild
docker-compose down; docker-compose up -d --build

# View logs to file
docker-compose up --build 2>&1 | Tee-Object -FilePath build.log

# Check running services
docker-compose ps
```

## Available Commands

The `start-docker.sh` script provides convenient commands:

```bash
./start-docker.sh up              # Start all services (production)
./start-docker.sh dev             # Start with development settings
./start-docker.sh build           # Build Docker images
./start-docker.sh down            # Stop all services
./start-docker.sh logs            # Show all logs
./start-docker.sh logs-frontend   # Frontend logs only
./start-docker.sh logs-backend    # Backend logs only
./start-docker.sh logs-db         # Database logs only
./start-docker.sh shell-frontend  # Access frontend container
./start-docker.sh shell-backend   # Access backend container
./start-docker.sh health          # Check service health
./start-docker.sh clean           # Clean up Docker resources
```

## Architecture

### Dockerfile Variants

The project provides multiple Dockerfile options for different use cases:

#### Backend: Dockerfile.unified (Recommended)
- **Status**: New unified multi-stage Dockerfile
- **Targets**: `dev` (development) and `production` (production/staging)
- **Features**:
  - Single source of truth for all environments
  - BuildKit optimized with cache mounts
  - Automatic dependency scope switching via build args
  - Smaller production images (232MB vs 245MB)
- **Usage**:
  ```bash
  # Development build
  docker build --file Dockerfile.unified --target dev --build-arg INSTALL_SCOPE=dev -t app:dev .

  # Production build
  docker build --file Dockerfile.unified --target production --build-arg INSTALL_SCOPE=main -t app:prod .
  ```

#### Frontend: Dockerfile.unified (Recommended)
- **Status**: New unified multi-stage Dockerfile for Next.js
- **Targets**: `dev` (development) and `runner` (production/staging)
- **Features**:
  - Single source of truth for all environments
  - BuildKit optimized with npm cache mounts
  - Next.js standalone mode for optimized production images
  - Production image: ~398MB (with security tools)
- **Usage**:
  ```bash
  cd frontend
  # Development build
  docker build --file Dockerfile.unified --target dev -t frontend:dev .

  # Production build (standalone mode)
  docker build --file Dockerfile.unified --target runner -t frontend:prod .
  ```

#### Legacy Dockerfiles
- **Dockerfile**: Original dev/production combined
- **Dockerfile.optimized**: BuildKit cache optimization focus
- **Dockerfile.production**: Production-only with minimal runtime
- **Status**: Maintained for backward compatibility during migration

### Services

#### Frontend Service (`frontend`)
- **Base Image**: Node.js 20 Alpine
- **Build**: Multi-stage build for optimized production image
- **Port**: 3000
- **Health Check**: `/api/health` endpoint
- **Environment**: Configurable via `.env.docker` and environment variables

#### Backend Service (`app`)
- **Base Image**: Python 3.11 slim (Dockerfile.unified)
- **Framework**: FastAPI with uvicorn
- **Port**: 8000
- **Dependencies**: Poetry 2.x for dependency management
- **Health Check**: Python built-in urllib (no curl dependency)

#### Database Service (`db`)
- **Image**: PostgreSQL 15
- **Port**: 5432
- **Storage**: Persistent volume (`postgres_data`)
- **Health Check**: `pg_isready` command

### Networking

Services communicate via Docker's internal network:
- Frontend → Backend: `http://app:8000`
- Backend → Database: `db:5432`

External access via published ports:
- Frontend: `localhost:3000` → `frontend:3000`
- Backend: `localhost:8000` → `app:8000`
- Database: `localhost:5432` → `db:5432`

## Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database
POSTGRES_SERVER=db
POSTGRES_USER=koiki_user
POSTGRES_PASSWORD=koiki_password
POSTGRES_DB=koiki_todo_db

# JWT
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

#### Frontend Environment Files

**For Docker (.env.docker)** - Used automatically in Docker containers:
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://app:8000

# Application
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

**For Local Development (.env.local)** - Copy from template for non-Docker development:
```bash
# API Configuration (direct connection to backend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development settings
NODE_ENV=development
NEXT_PUBLIC_ENABLE_DEV_TOOLS=true
NEXT_PUBLIC_DEBUG=false
```

### Development vs Production

#### Development Mode
- Hot reload enabled for both frontend and backend
- Volume mounts for source code
- Debug tools enabled
- Verbose logging

#### Production Mode
- Optimized builds
- No volume mounts for source code
- Security headers enabled
- Minimal logging

## File Structure

```
【Recommended - Unified Dockerfile Configurations】
├── docker-compose.unified.yml        # ★ Production/Staging (Dockerfile.unified)
├── docker-compose.unified.dev.yml    # ★ Development (Dockerfile.unified)
├── docker-compose.base.yml           # Common base definitions (for future)

【Legacy - Backward Compatibility】
├── docker-compose.yml                # Main Docker Compose configuration
├── docker-compose.dev.yml            # Development overrides
├── docker-compose.optimized.yml      # Optimized build configuration
├── docker-compose.production.yml     # Production configuration

【Scripts and Tools】
├── start-docker.sh                   # Startup script (Bash)
├── start-docker.ps1                  # Startup script (PowerShell)
├── scripts/
│   ├── verify-dockerfile-unified.sh  # Backend build verification (Bash)
│   ├── verify-dockerfile-unified.ps1 # Backend build verification (PowerShell)
│   ├── verify-frontend-unified.sh    # Frontend build verification (Bash)
│   └── verify-frontend-unified.ps1   # Frontend build verification (PowerShell)

【Dockerfiles】
├── Dockerfile                        # Backend Dockerfile (legacy)
├── Dockerfile.unified                # ★ Backend Dockerfile (recommended)
├── Dockerfile.optimized              # Backend Dockerfile (BuildKit optimized)
├── Dockerfile.production             # Backend Dockerfile (production only)
├── frontend/
│   ├── Dockerfile                    # Frontend Dockerfile (legacy)
│   ├── Dockerfile.unified            # ★ Frontend Dockerfile (recommended)
│   ├── Dockerfile.optimized          # Frontend Dockerfile (optimized)
│   ├── Dockerfile.production         # Frontend Dockerfile (production)
│   ├── .dockerignore                 # Docker ignore rules
│   ├── .env.docker                   # Docker environment
│   └── .env.local.example            # Local development template

【Documentation】
└── DOCKER_SETUP.md                  # This documentation
```

## Testing Dockerfile.unified

### Verification Script

Run the comprehensive build verification:

```bash
# Bash (Linux/macOS/WSL)
bash scripts/verify-dockerfile-unified.sh

# PowerShell (Windows)
powershell -ExecutionPolicy Bypass -File scripts/verify-dockerfile-unified.ps1
```

This script will:
1. Build dev target with development dependencies
2. Build production target with main dependencies only
3. Compare image sizes
4. Test BuildKit cache effectiveness

### Manual Testing

**Linux/macOS (Bash):**
```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Test development build
docker build --file Dockerfile.unified --target dev --tag test:dev .

# Test production build
docker build --file Dockerfile.unified --target production --tag test:prod .

# Test with docker-compose
docker-compose -f docker-compose.unified.dev.yml up --build
```

**Windows (PowerShell):**
```powershell
# Enable BuildKit
$env:DOCKER_BUILDKIT="1"

# Test development build
docker build --file Dockerfile.unified --target dev --tag test:dev .

# Test production build
docker build --file Dockerfile.unified --target production --tag test:prod .

# Test with docker-compose
docker-compose -f docker-compose.unified.dev.yml up --build
```

### Expected Results

**Backend:**
- **Dev image size**: ~340MB (includes dev dependencies)
- **Production image size**: ~232MB (main dependencies only)
- **Build time improvement**: 50-70% faster on second build (cache hit)

**Frontend:**
- **Dev image size**: ~1.11GB (includes full node_modules with devDependencies)
- **Runner image size**: ~398MB (Next.js standalone mode with security tools)
- **Build time improvement**: 60-80% faster on second build (npm cache hit)

## Development Workflow

### Initial Setup
1. Clone repository
2. Copy environment templates
3. Run `./start-docker.sh dev`

### Using Unified Configurations (Recommended)

**Development Environment (Linux/macOS):**
```bash
# Start development environment with Dockerfile.unified
docker-compose -f docker-compose.unified.dev.yml up --build

# Or using DOCKER_BUILDKIT explicitly
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.unified.dev.yml up --build

# Stop services
docker-compose -f docker-compose.unified.dev.yml down

# Clean up volumes
docker-compose -f docker-compose.unified.dev.yml down -v
```

**Development Environment (Windows PowerShell):**
```powershell
# Start development environment with Dockerfile.unified
docker-compose -f docker-compose.unified.dev.yml up --build

# Or using DOCKER_BUILDKIT explicitly
$env:DOCKER_BUILDKIT="1"
docker-compose -f docker-compose.unified.dev.yml up --build

# Stop services
docker-compose -f docker-compose.unified.dev.yml down

# Clean up volumes
docker-compose -f docker-compose.unified.dev.yml down -v
```

**Production/Staging Environment (Linux/macOS):**
```bash
# Start production environment with Dockerfile.unified
docker-compose -f docker-compose.unified.yml up --build

# Or with explicit BuildKit
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.unified.yml up --build

# Stop services
docker-compose -f docker-compose.unified.yml down
```

**Production/Staging Environment (Windows PowerShell):**
```powershell
# Start production environment with Dockerfile.unified
docker-compose -f docker-compose.unified.yml up --build

# Or with explicit BuildKit
$env:DOCKER_BUILDKIT="1"
docker-compose -f docker-compose.unified.yml up --build

# Stop services
docker-compose -f docker-compose.unified.yml down
```

**Using Legacy Configurations:**
```bash
# Legacy development environment (for backward compatibility)
docker-compose -f docker-compose.dev.yml up --build

# Legacy production environment
docker-compose -f docker-compose.production.yml up --build
```

### Making Changes
- **Frontend**: Changes automatically reload (development mode)
- **Backend**: Changes automatically reload (development mode with volume mounts)
- **Database**: Use Alembic migrations for schema changes

### Database Management
```bash
# Access database container
./start-docker.sh shell-backend

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## Troubleshooting

### Common Issues

#### Port Conflicts

**Linux/macOS:**
```bash
# Check port usage
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Stop conflicting services
./start-docker.sh down
```

**Windows (PowerShell):**
```powershell
# Check port usage
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Stop conflicting services
.\start-docker.ps1 down
# Or directly with docker-compose
docker-compose down
```

#### Build Failures

**Linux/macOS:**
```bash
# Clean rebuild
./start-docker.sh clean
./start-docker.sh build
```

**Windows (PowerShell):**
```powershell
# Clean rebuild
.\start-docker.ps1 clean
.\start-docker.ps1 build

# Or manually
docker system prune -af --volumes
docker-compose build --no-cache
```

#### Permission Issues

**Linux/macOS:**
```bash
# Fix file permissions
chmod +x start-docker.sh
sudo chown -R $USER:$USER frontend/node_modules
```

**Windows (PowerShell):**
```powershell
# Usually not needed on Windows, but if permission errors occur:
icacls frontend\node_modules /grant:r "$($env:USERNAME):(OI)(CI)F" /T
```

#### Health Check Failures
```bash
# Check service status
./start-docker.sh health

# View specific service logs
./start-docker.sh logs-frontend
./start-docker.sh logs-backend
./start-docker.sh logs-db
```

### Debugging

#### Container Shell Access
```bash
# Frontend container
./start-docker.sh shell-frontend

# Backend container
./start-docker.sh shell-backend

# Database queries
docker-compose exec db psql -U koiki_user -d koiki_todo_db
```

#### Log Analysis
```bash
# Real-time logs
./start-docker.sh logs

# Specific service logs
docker-compose logs -f frontend
docker-compose logs -f app
docker-compose logs -f db
```

## Security Considerations

### Production Deployment
- Change default passwords in `.env`
- Use strong JWT secrets
- Enable HTTPS (reverse proxy recommended)
- Restrict database access
- Regular security updates

### Network Security
- Internal service communication only
- Published ports only for external access
- Security headers enabled in production

## Performance Optimization

### Frontend
- Standalone output for smaller image size
- Multi-stage build for optimization
- Static file serving optimized

### Backend
- Poetry dependency caching
- Multi-stage build for smaller images
- Database connection pooling configured

### Database
- Optimized PostgreSQL settings
- Persistent volume for data
- Health checks for reliability

## Monitoring

### Health Checks
- Frontend: `/api/health`
- Backend: Built-in FastAPI monitoring
- Database: `pg_isready` command

### Logs
- Structured logging (JSON format)
- Service-specific log streams
- Development vs production log levels

## Backup and Recovery

### Database Backup

**Linux/macOS:**
```bash
# Create backup
docker-compose exec db pg_dump -U koiki_user koiki_todo_db > backup.sql

# Restore backup
docker-compose exec -T db psql -U koiki_user koiki_todo_db < backup.sql
```

**Windows (PowerShell):**
```powershell
# Create backup
docker-compose exec db pg_dump -U koiki_user koiki_todo_db | Out-File -Encoding UTF8 backup.sql

# Restore backup
Get-Content backup.sql | docker-compose exec -T db psql -U koiki_user koiki_todo_db
```

### Volume Management

**Linux/macOS:**
```bash
# List volumes
docker volume ls

# Backup volume
docker run --rm -v koiki-pyfw_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v koiki-pyfw_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

**Windows (PowerShell):**
```powershell
# List volumes
docker volume ls

# Backup volume
docker run --rm -v koiki-pyfw_postgres_data:/data -v ${PWD}:/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v koiki-pyfw_postgres_data:/data -v ${PWD}:/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```
