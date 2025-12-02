# verify-dockerfile-unified.ps1
# Dockerfile.unified verification script for Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Dockerfile.unified Verification Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Enable BuildKit
$env:DOCKER_BUILDKIT = "1"

function Print-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Print-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

try {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. Development Build (dev target)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "Building dev target..."

    $devBuildTime = Measure-Command {
        docker build `
            --file Dockerfile.unified `
            --target dev `
            --build-arg INSTALL_SCOPE=dev `
            --build-arg POETRY_MAX_WORKERS=10 `
            --tag koiki-pyfw-app:dev-unified `
            .
    }

    Print-Success "Dev build completed (Time: $($devBuildTime.TotalSeconds) seconds)"
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "2. Production Build (production target)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "Building production target..."

    $prodBuildTime = Measure-Command {
        docker build `
            --file Dockerfile.unified `
            --target production `
            --build-arg INSTALL_SCOPE=main `
            --build-arg POETRY_MAX_WORKERS=4 `
            --tag koiki-pyfw-app:prod-unified `
            .
    }

    Print-Success "Production build completed (Time: $($prodBuildTime.TotalSeconds) seconds)"
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "3. Image Size Comparison" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "Comparing with existing Dockerfiles..."
    Write-Host ""
    Write-Host "[Unified Dockerfile]" -ForegroundColor Yellow
    docker images | Select-String "koiki-pyfw-app.*unified"
    Write-Host ""
    Write-Host "[Legacy Dockerfiles]" -ForegroundColor Yellow
    docker images | Select-String "koiki-pyfw-app" | Select-String -NotMatch "unified"
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "4. Cache Effectiveness Test (2nd build)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "Building production target again..."

    $cacheBuildTime = Measure-Command {
        docker build `
            --file Dockerfile.unified `
            --target production `
            --tag koiki-pyfw-app:prod-unified-cache-test `
            .
    }

    Print-Success "Cache test completed"
    Write-Host "  1st build: $($prodBuildTime.TotalSeconds) seconds" -ForegroundColor Cyan
    Write-Host "  2nd build: $($cacheBuildTime.TotalSeconds) seconds" -ForegroundColor Cyan
    Write-Host "  Time saved: $($prodBuildTime.TotalSeconds - $cacheBuildTime.TotalSeconds) seconds" -ForegroundColor Green
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "5. Verification Complete" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Success "All builds completed successfully"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  - Test dev target with: docker-compose.unified.dev.yml"
    Write-Host "  - Test production target with: docker-compose.unified.yml"
    Write-Host ""

} catch {
    Print-Error "Build failed: $_"
    exit 1
}
