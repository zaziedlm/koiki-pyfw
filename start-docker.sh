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
    echo "  $0 up              - Start all services (production mode)"
    echo "  $0 dev             - Start all services (development mode with hot reload)"
    echo "  $0 build           - Build all Docker images"
    echo "  $0 down            - Stop and remove all containers"
    echo "  $0 logs            - Show logs from all services"
    echo "  $0 logs-frontend   - Show frontend logs only"
    echo "  $0 logs-backend    - Show backend logs only"
    echo "  $0 logs-db         - Show database logs only"
    echo "  $0 shell-frontend  - Access frontend container shell"
    echo "  $0 shell-backend   - Access backend container shell"
    echo "  $0 health          - Check health of all services"
    echo "  $0 clean           - Clean up Docker resources"
    echo ""
}

# Parse command
case "${1:-up}" in
    "up")
        echo "🏗️  Starting services in production mode..."
        docker-compose up -d
        echo "✅ Services started!"
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔗 Backend API: http://localhost:8000"
        echo "📊 API Docs: http://localhost:8000/docs"
        ;;
    "dev")
        echo "🛠️  Starting services in development mode..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
        ;;
    "build")
        echo "🏗️  Building Docker images..."
        docker-compose build
        echo "✅ Build completed!"
        ;;
    "down")
        echo "🛑 Stopping services..."
        docker-compose down
        echo "✅ Services stopped!"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "logs-frontend")
        docker-compose logs -f frontend
        ;;
    "logs-backend")
        docker-compose logs -f app
        ;;
    "logs-db")
        docker-compose logs -f db
        ;;
    "shell-frontend")
        echo "🐚 Accessing frontend container..."
        docker-compose exec frontend sh
        ;;
    "shell-backend")
        echo "🐚 Accessing backend container..."
        docker-compose exec app bash
        ;;
    "health")
        echo "🏥 Checking service health..."
        echo "Frontend health:"
        curl -s http://localhost:3000/api/health | jq . || echo "❌ Frontend not responding"
        echo "Backend health:"
        curl -s http://localhost:8000/api/health || echo "❌ Backend not responding"
        echo "Database health:"
        docker-compose exec db pg_isready -U ${POSTGRES_USER:-koiki_user} -d ${POSTGRES_DB:-koiki_todo_db} || echo "❌ Database not responding"
        ;;
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose down -v
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