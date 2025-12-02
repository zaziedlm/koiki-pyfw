# verify-frontend-unified.ps1
# frontend/Dockerfile.unifiedの動作検証スクリプト (Windows PowerShell版)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Frontend Dockerfile.unified 検証スクリプト" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Enable BuildKit
$env:DOCKER_BUILDKIT = "1"

function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Change to frontend directory
Set-Location frontend

try {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. 開発環境ビルド (dev target)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "Building dev target..."

    $devBuildTime = Measure-Command {
        docker build `
            --file Dockerfile.unified `
            --target dev `
            --tag koiki-pyfw-frontend:dev-unified `
            .
    }

    Print-Success "開発環境ビルド成功 (所要時間: $($devBuildTime.TotalSeconds)秒)"
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "2. 本番環境ビルド (runner target)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "Building runner target..."

    $runnerBuildTime = Measure-Command {
        docker build `
            --file Dockerfile.unified `
            --target runner `
            --tag koiki-pyfw-frontend:runner-unified `
            .
    }

    Print-Success "本番環境ビルド成功 (所要時間: $($runnerBuildTime.TotalSeconds)秒)"
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "3. イメージサイズ比較" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "既存Dockerfileとの比較..."
    Write-Host ""
    Write-Host "【統一Dockerfile】" -ForegroundColor Yellow
    docker images | Select-String "koiki-pyfw-frontend.*unified"
    Write-Host ""
    Write-Host "【既存Dockerfile】" -ForegroundColor Yellow
    docker images | Select-String "koiki-pyfw-frontend" | Select-String -NotMatch "unified"
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "4. キャッシュ効果確認（2回目ビルド）" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Info "2回目のrunner targetビルド..."

    $cacheBuildTime = Measure-Command {
        docker build `
            --file Dockerfile.unified `
            --target runner `
            --tag koiki-pyfw-frontend:runner-unified-cache-test `
            .
    }

    Print-Success "キャッシュ効果確認成功"
    Write-Host "  1回目: $($runnerBuildTime.TotalSeconds)秒" -ForegroundColor Cyan
    Write-Host "  2回目: $($cacheBuildTime.TotalSeconds)秒" -ForegroundColor Cyan
    Write-Host "  削減: $($runnerBuildTime.TotalSeconds - $cacheBuildTime.TotalSeconds)秒" -ForegroundColor Green
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "5. ビルド検証完了" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Print-Success "全てのビルドが正常に完了しました"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  - Test dev target with: docker-compose.unified.dev.yml"
    Write-Host "  - Test runner target with: docker-compose.unified.yml"
    Write-Host ""

} catch {
    Write-Host "[ERROR] Build failed: $_" -ForegroundColor Red
    exit 1
} finally {
    # Return to parent directory
    Set-Location ..
}
