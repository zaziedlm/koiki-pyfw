#!/bin/bash

# KOIKI Framework Docker Compose Startup Script

set -e

echo "[INFO] Starting KOIKI Framework with Docker Compose..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARN] .env not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "[INFO] Please edit .env with your configuration"
    else
        echo "[ERROR] .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if frontend .env.local exists for local development
if [ ! -f frontend/.env.local ]; then
    echo "[INFO] Creating frontend .env.local from template..."
    cp frontend/.env.local.example frontend/.env.local
    echo "[INFO] Frontend .env.local created"
fi

# Function to show available commands
show_help() {
    echo ""
    echo "Available commands:"
    echo "  Production mode:"
    echo "    $0 up              - Start all services (production mode)"
    echo "    $0 build           - Build all Docker images (production)"
    echo "    $0 down            - Stop and remove all containers (production)"
    echo "    $0 logs            - Show logs from all services (production)"
    echo "    $0 logs-frontend   - Show frontend logs only (production)"
    echo "    $0 logs-backend    - Show backend logs only (production)"
    echo "    $0 logs-db         - Show database logs only (production)"
    echo "    $0 shell-frontend  - Access frontend container shell (production)"
    echo "    $0 shell-backend   - Access backend container shell (production)"
    echo ""
    echo "  Development mode:"
    echo "    $0 dev             - Start all services (development with hot reload)"
    echo "    $0 build-dev       - Build all Docker images (development)"
    echo "    $0 down-dev        - Stop and remove all containers (development)"
    echo "    $0 logs-dev        - Show logs from all services (development)"
    echo "    $0 logs-frontend-dev   - Show frontend logs only (development)"
    echo "    $0 logs-backend-dev    - Show backend logs only (development)"
    echo "    $0 logs-db-dev         - Show database logs only (development)"
    echo "    $0 shell-frontend-dev  - Access frontend container shell (development)"
    echo "    $0 shell-backend-dev   - Access backend container shell (development)"
    echo ""
    echo "  Unified (profiles: dev / optimized / prod / prod-external):"
    echo "    $0 unified-dev            - Start unified stack (dev profile, foreground)"
    echo "    $0 unified-dev-build      - Build unified stack images (dev profile)"
    echo "    $0 unified-dev-down       - Stop unified stack (dev profile)"
    echo "    $0 unified-optimized      - Start unified stack (optimized profile, detached)"
    echo "    $0 unified-optimized-build - Build unified stack images (optimized profile)"
    echo "    $0 unified-optimized-down - Stop unified stack (optimized profile)"
    echo "    $0 unified-prod           - Start unified stack (prod profile, detached)"
    echo "    $0 unified-prod-build     - Build unified stack images (prod profile)"
    echo "    $0 unified-prod-down      - Stop unified stack (prod profile)"
    echo "    $0 unified-prod-external  - Start unified stack (prod-external profile, detached)"
    echo "    $0 unified-prod-external-build - Build unified stack images (prod-external profile)"
    echo "    $0 unified-prod-external-down  - Stop unified stack (prod-external profile)"
    echo "    $0 unified-down           - Stop unified stack"
    echo "    $0 unified-logs           - Tail unified logs"
    echo ""
    echo "  General:"
    echo "    $0 health          - Check health of all services"
    echo "    $0 clean           - Clean up Docker resources"
    echo ""
}

# Parse command
case "${1:-up}" in
    "up")
        echo "[INFO] Starting services in production mode..."
        docker compose up -d
        echo "[INFO] Services started"
        echo "[INFO] Frontend: http://localhost:3000"
        echo "[INFO] Backend API: http://localhost:8000"
        echo "[INFO] API Docs: http://localhost:8000/docs"
        ;;
    "dev")
        echo "[INFO] Starting services in development mode..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up
        ;;
    "build")
        echo "[INFO] Building Docker images (production)..."
        docker compose build
        echo "[INFO] Build completed"
        ;;
    "build-dev")
        echo "[INFO] Building Docker images (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml build
        echo "[INFO] Development build completed"
        ;;
    "down")
        echo "[INFO] Stopping services (production)..."
        docker compose down
        echo "[INFO] Services stopped"
        ;;
    "down-dev")
        echo "[INFO] Stopping services (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml down
        echo "[INFO] Services stopped"
        ;;
    "logs")
        docker compose logs -f
        ;;
    "logs-dev")
        docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
        ;;
    "logs-frontend")
        docker compose logs -f frontend
        ;;
    "logs-frontend-dev")
        docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f frontend
        ;;
    "logs-backend")
        docker compose logs -f app
        ;;
    "logs-backend-dev")
        docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f app
        ;;
    "logs-db")
        docker compose logs -f db
        ;;
    "logs-db-dev")
        docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f db
        ;;
    "shell-frontend")
        echo "[INFO] Accessing frontend container (production)..."
        docker compose exec frontend sh
        ;;
    "shell-frontend-dev")
        echo "[INFO] Accessing frontend container (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend sh
        ;;
    "shell-backend")
        echo "[INFO] Accessing backend container (production)..."
        docker compose exec app bash
        ;;
    "shell-backend-dev")
        echo "[INFO] Accessing backend container (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app bash
        ;;
    "health")
        echo "[INFO] Checking service health..."
        echo "Frontend health:"
        curl -s http://localhost:3000/api/health | jq . || echo "[WARN] Frontend not responding"
        echo "Backend health:"
        curl -s http://localhost:8000/api/health || echo "[WARN] Backend not responding"
        echo "Database health:"
        docker compose exec db pg_isready -U ${POSTGRES_USER:-koiki_user} -d ${POSTGRES_DB:-koiki_todo_db} || echo "[WARN] Database not responding"
        ;;
    "clean")
        echo "[INFO] Cleaning up Docker resources..."
        docker compose down -v
        docker system prune -f
        echo "[INFO] Cleanup completed"
        ;;
    "unified-dev")
        echo "[INFO] Starting unified stack (dev profile)..."
        ENV_FILE=${ENV_FILE:-.env} docker compose -f docker-compose.unified.yml --profile dev up
        ;;
    "unified-dev-build")
        echo "[INFO] Building unified stack images (dev profile)..."
        ENV_FILE=${ENV_FILE:-.env} docker compose -f docker-compose.unified.yml --profile dev build
        ;;
    "unified-dev-down")
        echo "[INFO] Stopping unified stack (dev profile)..."
        ENV_FILE=${ENV_FILE:-.env} docker compose -f docker-compose.unified.yml --profile dev down
        ;;
    "unified-optimized")
        echo "[INFO] Starting unified stack (optimized profile)..."
        ENV_FILE=${ENV_FILE:-.env} docker compose -f docker-compose.unified.yml --profile optimized up -d
        ;;
    "unified-optimized-build")
        echo "[INFO] Building unified stack images (optimized profile)..."
        ENV_FILE=${ENV_FILE:-.env} docker compose -f docker-compose.unified.yml --profile optimized build
        ;;
    "unified-optimized-down")
        echo "[INFO] Stopping unified stack (optimized profile)..."
        ENV_FILE=${ENV_FILE:-.env} docker compose -f docker-compose.unified.yml --profile optimized down
        ;;
    "unified-prod")
        echo "[INFO] Starting unified stack (prod profile)..."
        ENV_FILE=${ENV_FILE:-.env.production} docker compose -f docker-compose.unified.yml --profile prod up -d
        ;;
    "unified-prod-build")
        echo "[INFO] Building unified stack images (prod profile)..."
        ENV_FILE=${ENV_FILE:-.env.production} docker compose -f docker-compose.unified.yml --profile prod build
        ;;
    "unified-prod-down")
        echo "[INFO] Stopping unified stack (prod profile)..."
        ENV_FILE=${ENV_FILE:-.env.production} docker compose -f docker-compose.unified.yml --profile prod down
        ;;
    "unified-prod-external")
        echo "[INFO] Starting unified stack (prod-external profile, external DB/IdP)..."
        ENV_FILE=${ENV_FILE:-.env.production} docker compose -f docker-compose.unified.yml --profile prod-external up -d
        ;;
    "unified-prod-external-build")
        echo "[INFO] Building unified stack images (prod-external profile)..."
        ENV_FILE=${ENV_FILE:-.env.production} docker compose -f docker-compose.unified.yml --profile prod-external build
        ;;
    "unified-prod-external-down")
        echo "[INFO] Stopping unified stack (prod-external profile)..."
        ENV_FILE=${ENV_FILE:-.env.production} docker compose -f docker-compose.unified.yml --profile prod-external down
        ;;
    "unified-down")
        echo "[INFO] Stopping unified stack..."
        # Stop all unified profiles so containers created with any profile are removed
        docker compose -f docker-compose.unified.yml --profile dev --profile optimized --profile prod --profile prod-external down
        ;;
    "unified-logs")
        echo "[INFO] Showing logs for unified stack..."
        docker compose -f docker-compose.unified.yml logs -f
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "[ERROR] Unknown command: $1"
        show_help
        exit 1
        ;;
esac
