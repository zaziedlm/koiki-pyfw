# KOIKI Framework Docker Compose Startup Script for PowerShell

param(
    [Parameter(Position=0)]
    [string]$Command = "up"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting KOIKI Framework with Docker Compose..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating from .env-sample..." -ForegroundColor Yellow
    if (Test-Path ".env-sample") {
        Copy-Item ".env-sample" ".env"
        Write-Host "📝 Please edit .env file with your configuration" -ForegroundColor Cyan
    } else {
        Write-Host "❌ No .env-sample found. Please create .env file manually." -ForegroundColor Red
        exit 1
    }
}

# Check if frontend .env.local exists for local development
if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "📝 Creating frontend environment configuration..." -ForegroundColor Cyan
    Copy-Item "frontend\.env.local.example" "frontend\.env.local"
    Write-Host "✅ Frontend .env.local created from template" -ForegroundColor Green
}

# Function to show available commands
function Show-Help {
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  .\start-docker.ps1 up              - Start all services (production mode)" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 dev             - Start all services (development mode with hot reload)" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 build           - Build all Docker images" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 down            - Stop and remove all containers" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 logs            - Show logs from all services" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 logs-frontend   - Show frontend logs only" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 logs-backend    - Show backend logs only" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 logs-db         - Show database logs only" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 shell-frontend  - Access frontend container shell" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 shell-backend   - Access backend container shell" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 health          - Check health of all services" -ForegroundColor White
    Write-Host "  .\start-docker.ps1 clean           - Clean up Docker resources" -ForegroundColor White
    Write-Host ""
}

# Parse command
switch ($Command.ToLower()) {
    "up" {
        Write-Host "🏗️  Starting services in production mode..." -ForegroundColor Blue
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Services started!" -ForegroundColor Green
            Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
            Write-Host "🔗 Backend API: http://localhost:8000" -ForegroundColor Cyan
            Write-Host "📊 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
        } else {
            Write-Host "❌ Failed to start services" -ForegroundColor Red
            exit 1
        }
    }
    "dev" {
        Write-Host "🛠️  Starting services in development mode..." -ForegroundColor Blue
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
    }
    "build" {
        Write-Host "🏗️  Building Docker images..." -ForegroundColor Blue
        docker-compose build
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Build completed!" -ForegroundColor Green
        } else {
            Write-Host "❌ Build failed" -ForegroundColor Red
            exit 1
        }
    }
    "down" {
        Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
        docker-compose down
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Services stopped!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to stop services" -ForegroundColor Red
            exit 1
        }
    }
    "logs" {
        docker-compose logs -f
    }
    "logs-frontend" {
        docker-compose logs -f frontend
    }
    "logs-backend" {
        docker-compose logs -f app
    }
    "logs-db" {
        docker-compose logs -f db
    }
    "shell-frontend" {
        Write-Host "🐚 Accessing frontend container..." -ForegroundColor Cyan
        docker-compose exec frontend sh
    }
    "shell-backend" {
        Write-Host "🐚 Accessing backend container..." -ForegroundColor Cyan
        docker-compose exec app bash
    }
    "health" {
        Write-Host "🏥 Checking service health..." -ForegroundColor Blue
        
        Write-Host "Frontend health:" -ForegroundColor Yellow
        try {
            $frontendHealth = Invoke-RestMethod -Uri "http://localhost:3000/api/health" -TimeoutSec 5
            $frontendHealth | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "❌ Frontend not responding" -ForegroundColor Red
        }
        
        Write-Host "Backend health:" -ForegroundColor Yellow
        try {
            $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5
            $backendHealth | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "❌ Backend not responding" -ForegroundColor Red
        }
        
        Write-Host "Database health:" -ForegroundColor Yellow
        try {
            # Get environment variables from .env file if available
            $postgresUser = "koiki_user"
            $postgresDb = "koiki_todo_db"
            
            if (Test-Path ".env") {
                $envContent = Get-Content ".env"
                foreach ($line in $envContent) {
                    if ($line -match "^POSTGRES_USER=(.+)$") {
                        $postgresUser = $matches[1]
                    }
                    if ($line -match "^POSTGRES_DB=(.+)$") {
                        $postgresDb = $matches[1]
                    }
                }
            }
            
            docker-compose exec db pg_isready -U $postgresUser -d $postgresDb
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Database is healthy" -ForegroundColor Green
            } else {
                Write-Host "❌ Database not responding" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Database not responding" -ForegroundColor Red
        }
    }
    "clean" {
        Write-Host "🧹 Cleaning up Docker resources..." -ForegroundColor Yellow
        docker-compose down -v
        docker system prune -f
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Cleanup completed!" -ForegroundColor Green
        } else {
            Write-Host "❌ Cleanup failed" -ForegroundColor Red
            exit 1
        }
    }
    { $_ -in @("help", "-h", "--help") } {
        Show-Help
    }
    default {
        Write-Host "❌ Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
