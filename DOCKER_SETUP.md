# KOIKI Framework Docker Setup

This document describes the Docker containerization setup for the KOIKI Framework, including both the Python FastAPI backend and Next.js frontend.

## Overview

The Docker setup includes:
- **Backend**: FastAPI application with PostgreSQL database
- **Frontend**: Next.js application with TypeScript and Tailwind CSS
- **Database**: PostgreSQL 15 with persistent storage
- **Networking**: Internal Docker network for service communication

## Quick Start

### 1. Environment Setup

```bash
# Copy environment templates
cp .env-sample .env
cp frontend/.env.local.example frontend/.env.local

# Edit configuration files as needed
# Backend configuration
nano .env

# Frontend local development configuration (customize as needed)
nano frontend/.env.local
# Common customizations:
# - NEXT_PUBLIC_API_URL: Change if backend runs on different port/host
# - NEXT_PUBLIC_DEBUG: Set to true for detailed logging
# - NEXT_PUBLIC_DEFAULT_THEME: Choose light, dark, or system
# Note: .env.local is for local non-Docker development
# Docker environments use .env.docker automatically
```

### 2. Start Services

```bash
# Production mode
./start-docker.sh up

# Development mode (with hot reload)
./start-docker.sh dev

# View logs
./start-docker.sh logs
```

### 3. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

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

### Services

#### Frontend Service (`frontend`)
- **Base Image**: Node.js 20 Alpine
- **Build**: Multi-stage build for optimized production image
- **Port**: 3000
- **Health Check**: `/api/health` endpoint
- **Environment**: Configurable via `.env.docker` and environment variables

#### Backend Service (`app`)
- **Base Image**: Python 3.13 Alpine
- **Framework**: FastAPI with uvicorn
- **Port**: 8000
- **Dependencies**: Poetry 2.x for dependency management
- **Health Check**: Built-in FastAPI health monitoring

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
├── docker-compose.yml           # Main Docker Compose configuration
├── docker-compose.dev.yml       # Development overrides
├── start-docker.sh             # Startup script
├── Dockerfile                  # Backend Dockerfile
├── frontend/
│   ├── Dockerfile              # Frontend Dockerfile
│   ├── .dockerignore           # Docker ignore rules
│   ├── .env.docker             # Docker environment
│   └── .env.local.example      # Local development template
└── DOCKER_SETUP.md            # This documentation
```

## Development Workflow

### Initial Setup
1. Clone repository
2. Copy environment templates
3. Run `./start-docker.sh dev`

### Making Changes
- **Frontend**: Changes automatically reload (development mode)
- **Backend**: Changes automatically reload (development mode)
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
```bash
# Check port usage
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Stop conflicting services
./start-docker.sh down
```

#### Build Failures
```bash
# Clean rebuild
./start-docker.sh clean
./start-docker.sh build
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x start-docker.sh
sudo chown -R $USER:$USER frontend/node_modules
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
```bash
# Create backup
docker-compose exec db pg_dump -U koiki_user koiki_todo_db > backup.sql

# Restore backup
docker-compose exec -T db psql -U koiki_user koiki_todo_db < backup.sql
```

### Volume Management
```bash
# List volumes
docker volume ls

# Backup volume
docker run --rm -v koiki-pyfw_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v koiki-pyfw_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```