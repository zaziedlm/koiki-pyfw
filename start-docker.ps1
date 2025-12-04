# KOIKI Framework Docker Compose Startup Script for PowerShell

param(
    [Parameter(Position=0)]
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"

Write-Host "[INFO] Starting KOIKI Framework with Docker Compose..."

# Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] .env not found. Creating from .env.example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[INFO] Please edit .env with your configuration"
    } else {
        Write-Host "[ERROR] .env.example not found. Create .env manually."
        exit 1
    }
}

# Ensure frontend .env.local exists
if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "[INFO] Creating frontend .env.local from template..."
    Copy-Item "frontend\.env.local.example" "frontend\.env.local"
    Write-Host "[INFO] Frontend .env.local created"
}

function Show-Help {
    Write-Host ""
    Write-Host "Available commands:"
    Write-Host "  Production mode:"
    Write-Host "    .\start-docker.ps1 up              - Start all services (production mode)"
    Write-Host "    .\start-docker.ps1 build           - Build all Docker images (production)"
    Write-Host "    .\start-docker.ps1 down            - Stop and remove all containers (production)"
    Write-Host "    .\start-docker.ps1 logs            - Show logs from all services (production)"
    Write-Host "    .\start-docker.ps1 logs-frontend   - Show frontend logs only (production)"
    Write-Host "    .\start-docker.ps1 logs-backend    - Show backend logs only (production)"
    Write-Host "    .\start-docker.ps1 logs-db         - Show database logs only (production)"
    Write-Host "    .\start-docker.ps1 shell-frontend  - Access frontend container shell (production)"
    Write-Host "    .\start-docker.ps1 shell-backend   - Access backend container shell (production)"
    Write-Host ""
    Write-Host "  Development mode:"
    Write-Host "    .\start-docker.ps1 dev             - Start all services (development with hot reload)"
    Write-Host "    .\start-docker.ps1 build-dev       - Build all Docker images (development)"
    Write-Host "    .\start-docker.ps1 down-dev        - Stop and remove all containers (development)"
    Write-Host "    .\start-docker.ps1 logs-dev        - Show logs from all services (development)"
    Write-Host "    .\start-docker.ps1 logs-frontend-dev   - Show frontend logs only (development)"
    Write-Host "    .\start-docker.ps1 logs-backend-dev    - Show backend logs only (development)"
    Write-Host "    .\start-docker.ps1 logs-db-dev         - Show database logs only (development)"
    Write-Host "    .\start-docker.ps1 shell-frontend-dev  - Access frontend container shell (development)"
    Write-Host "    .\start-docker.ps1 shell-backend-dev   - Access backend container shell (development)"
    Write-Host ""
    Write-Host "  Unified (profiles: dev / optimized / prod / prod-external):"
    Write-Host "    .\start-docker.ps1 unified-dev            - Start unified stack (dev profile, foreground)"
    Write-Host "    .\start-docker.ps1 unified-optimized      - Start unified stack (optimized profile, detached)"
    Write-Host "    .\start-docker.ps1 unified-prod           - Start unified stack (prod profile, detached)"
    Write-Host "    .\start-docker.ps1 unified-prod-external  - Start unified stack (prod-external profile, detached)"
    Write-Host "    .\start-docker.ps1 unified-down           - Stop unified stack"
    Write-Host "    .\start-docker.ps1 unified-logs           - Tail unified logs"
    Write-Host ""
    Write-Host "  General:"
    Write-Host "    .\start-docker.ps1 health          - Check health of all services"
    Write-Host "    .\start-docker.ps1 clean           - Clean up Docker resources"
    Write-Host ""
}

switch ($Command.ToLower()) {
    "up" {
        Write-Host "[INFO] Starting services in production mode..."
        docker compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Services started"
            Write-Host "[INFO] Frontend: http://localhost:3000"
            Write-Host "[INFO] Backend API: http://localhost:8000"
            Write-Host "[INFO] API Docs: http://localhost:8000/docs"
        } else {
            Write-Host "[ERROR] Failed to start services"
            exit 1
        }
    }
    "dev" {
        Write-Host "[INFO] Starting services in development mode..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up
    }
    "build" {
        Write-Host "[INFO] Building Docker images (production)..."
        docker compose build
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Build completed"
        } else {
            Write-Host "[ERROR] Build failed"
            exit 1
        }
    }
    "build-dev" {
        Write-Host "[INFO] Building Docker images (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml build
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Development build completed"
        } else {
            Write-Host "[ERROR] Build failed"
            exit 1
        }
    }
    "down" {
        Write-Host "[INFO] Stopping services (production)..."
        docker compose down
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Services stopped"
        } else {
            Write-Host "[ERROR] Failed to stop services"
            exit 1
        }
    }
    "down-dev" {
        Write-Host "[INFO] Stopping services (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml down
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Services stopped"
        } else {
            Write-Host "[ERROR] Failed to stop services"
            exit 1
        }
    }
    "logs" { docker compose logs -f }
    "logs-dev" { docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f }
    "logs-frontend" { docker compose logs -f frontend }
    "logs-frontend-dev" { docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f frontend }
    "logs-backend" { docker compose logs -f app }
    "logs-backend-dev" { docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f app }
    "logs-db" { docker compose logs -f db }
    "logs-db-dev" { docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f db }
    "shell-frontend" {
        Write-Host "[INFO] Accessing frontend container (production)..."
        docker compose exec frontend sh
    }
    "shell-frontend-dev" {
        Write-Host "[INFO] Accessing frontend container (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend sh
    }
    "shell-backend" {
        Write-Host "[INFO] Accessing backend container (production)..."
        docker compose exec app bash
    }
    "shell-backend-dev" {
        Write-Host "[INFO] Accessing backend container (development)..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app bash
    }
    "health" {
        Write-Host "[INFO] Checking service health..."

        Write-Host "Frontend health:"
        try {
            $frontendHealth = Invoke-RestMethod -Uri "http://localhost:3000/api/health" -TimeoutSec 5
            $frontendHealth | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "[WARN] Frontend not responding"
        }

        Write-Host "Backend health:"
        try {
            $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5
            $backendHealth | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "[WARN] Backend not responding"
        }

        Write-Host "Database health:"
        try {
            $postgresUser = "koiki_user"
            $postgresDb = "koiki_todo_db"

            if (Test-Path ".env") {
                $envContent = Get-Content ".env"
                foreach ($line in $envContent) {
                    if ($line -match "^POSTGRES_USER=(.+)$") { $postgresUser = $matches[1] }
                    if ($line -match "^POSTGRES_DB=(.+)$") { $postgresDb = $matches[1] }
                }
            }

            docker compose exec db pg_isready -U $postgresUser -d $postgresDb
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[INFO] Database is healthy"
            } else {
                Write-Host "[WARN] Database not responding"
            }
        } catch {
            Write-Host "[WARN] Database not responding"
        }
    }
    "clean" {
        Write-Host "[INFO] Cleaning up Docker resources..."
        docker compose down -v
        docker system prune -f
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Cleanup completed"
        } else {
            Write-Host "[ERROR] Cleanup failed"
            exit 1
        }
    }
    "unified-dev" {
        Write-Host "[INFO] Starting unified stack (dev profile)..."
        $env:ENV_FILE = ".env"
        docker compose -f docker-compose.unified.yml --profile dev up
    }
    "unified-optimized" {
        Write-Host "[INFO] Starting unified stack (optimized profile)..."
        $env:ENV_FILE = ".env"
        docker compose -f docker-compose.unified.yml --profile optimized up -d
    }
    "unified-prod" {
        Write-Host "[INFO] Starting unified stack (prod profile)..."
        $env:ENV_FILE = ".env.production"
        docker compose -f docker-compose.unified.yml --profile prod up -d
    }
    "unified-prod-external" {
        Write-Host "[INFO] Starting unified stack (prod-external profile, external DB/IdP)..."
        $env:ENV_FILE = ".env.production"
        docker compose -f docker-compose.unified.yml --profile prod-external up -d
    }
    "unified-down" {
        Write-Host "[INFO] Stopping unified stack..."
        # Stop all unified profiles so containers created with any profile are removed
        docker compose -f docker-compose.unified.yml --profile dev --profile optimized --profile prod --profile prod-external down
    }
    "unified-logs" {
        Write-Host "[INFO] Showing logs for unified stack..."
        docker compose -f docker-compose.unified.yml logs -f
    }
    { $_ -in @("help", "-h", "--help") } {
        Show-Help
    }
    default {
        Write-Host "[ERROR] Unknown command: $Command"
        Show-Help
        exit 1
    }
}
