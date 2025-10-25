#!/bin/bash

# KOIKI Framework Docker Compose Startup Script

set -e

echo "🚀 Starting KOIKI Framework with Docker Compose..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your configuration"
    else
        echo "❌ No .env.example found. Please create .env file manually."
        exit 1
    fi
fi

# Check if frontend .env.local exists for local development
if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend environment configuration..."
    cp frontend/.env.local.example frontend/.env.local
    echo "✅ Frontend .env.local created from template"
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
    echo "    $0 dev             - Start all services (development mode with hot reload)"
    echo "    $0 build-dev       - Build all Docker images (development)"
    echo "    $0 down-dev        - Stop and remove all containers (development)"
    echo "    $0 logs-dev        - Show logs from all services (development)"
    echo "    $0 logs-frontend-dev   - Show frontend logs only (development)"
    echo "    $0 logs-backend-dev    - Show backend logs only (development)"
    echo "    $0 logs-db-dev         - Show database logs only (development)"
    echo "    $0 shell-frontend-dev  - Access frontend container shell (development)"
    echo "    $0 shell-backend-dev   - Access backend container shell (development)"
    echo ""
    echo "  General:"
    echo "    $0 health          - Check health of all services"
    echo "    $0 clean           - Clean up Docker resources"
    echo ""
}

# Parse command
case "${1:-up}" in
    "up")
        echo "🏗️  Starting services in production mode..."
        docker compose up -d
        echo "✅ Services started!"
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔗 Backend API: http://localhost:8000"
        echo "📊 API Docs: http://localhost:8000/docs"
        ;;
    "dev")
        echo "🛠️  Starting services in development mode..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up
        ;;
    "build")
        echo "🏗️  Building Docker images (production)..."
        docker compose build
        echo "✅ Build completed!"
        ;;
    "build-dev")
        echo "🏗️  Building Docker images (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml build
        echo "✅ Development build completed!"
        ;;
    "down")
        echo "🛑 Stopping services (production)..."
        docker compose down
        echo "✅ Services stopped!"
        ;;
    "down-dev")
        echo "🛑 Stopping services (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml down
        echo "✅ Services stopped!"
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
        echo "🐚 Accessing frontend container (production)..."
        docker compose exec frontend sh
        ;;
    "shell-frontend-dev")
        echo "🐚 Accessing frontend container (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend sh
        ;;
    "shell-backend")
        echo "🐚 Accessing backend container (production)..."
        docker compose exec app bash
        ;;
    "shell-backend-dev")
        echo "🐚 Accessing backend container (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app bash
        ;;
    "health")
        echo "🏥 Checking service health..."
        echo "Frontend health:"
        curl -s http://localhost:3000/api/health | jq . || echo "❌ Frontend not responding"
        echo "Backend health:"
        curl -s http://localhost:8000/api/health || echo "❌ Backend not responding"
        echo "Database health:"
        docker compose exec db pg_isready -U ${POSTGRES_USER:-koiki_user} -d ${POSTGRES_DB:-koiki_todo_db} || echo "❌ Database not responding"
        ;;
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker compose down -v
        docker system prune -f
        echo "✅ Cleanup completed!"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac