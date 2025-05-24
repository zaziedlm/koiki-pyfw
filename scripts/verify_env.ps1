#!/usr/bin/env pwsh
# verify_env.ps1 - KOIKI-FW環境検証スクリプト

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

Write-Host "=== KOIKI-FW 環境検証 ===" -ForegroundColor Cyan
Write-Host "バージョン: 0.3.0" -ForegroundColor Cyan
Write-Host "実行時刻: $(Get-Date)" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# プロジェクトルートディレクトリのパスを取得
$rootDir = Split-Path -Parent $PSScriptRoot

# プロジェクトルートディレクトリに移動
Push-Location $rootDir

try {
    # Poetryが利用可能か確認
    $poetryInstalled = $null -ne (Get-Command poetry -ErrorAction SilentlyContinue)
    if (-not $poetryInstalled) {
        Write-Host "✗ Poetry がインストールされていません。init_poetry_env.ps1 を実行してください。" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Poetry が利用可能です" -ForegroundColor Green
    
    # 仮想環境の確認
    $venvPath = ".\.venv"
    if (-not (Test-Path -Path $venvPath -PathType Container)) {
        Write-Host "✗ Poetry 仮想環境がありません。init_poetry_env.ps1 を実行してください。" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Poetry 仮想環境が存在します" -ForegroundColor Green

    # Python実行ファイルの場所を確認
    Write-Host "`n== Python Environment ==" -ForegroundColor Green
    $pythonPath = & poetry run which python 2>$null
    if (-not $pythonPath) {
        $pythonPath = & poetry run python -c "import sys; print(sys.executable)"
    }
    Write-Host "Python Path: $pythonPath"
    $pythonVersion = & poetry run python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    Write-Host "Python Version: $pythonVersion"
    
    # Poetry環境の状態を確認
    Write-Host "`n== Poetry Environment ==" -ForegroundColor Green
    & poetry env info
    
    # インストールされたパッケージの確認
    Write-Host "`n== Installed Packages ==" -ForegroundColor Green
    & poetry show

    # libkoikiのインポート確認
    Write-Host "`n== Testing libkoiki import ==" -ForegroundColor Green
    try {
        $libkoikiVersion = & poetry run python -c "import libkoiki; print(f' libkoiki version: {libkoiki.__version__}')"
        Write-Host $libkoikiVersion -ForegroundColor Green
    }
    catch {
        Write-Host "✗ libkoikiのインポートに失敗しました: $_" -ForegroundColor Red
    }
    
    # 重要なパッケージの確認
    Write-Host "`n== Checking Key Dependencies ==" -ForegroundColor Green
    $packages = @(
        "fastapi", 
        "uvicorn", 
        "sqlalchemy", 
        "pydantic", 
        "pytest", 
        "structlog", 
        "pydantic-settings"
    )
    
    foreach ($pkg in $packages) {
        $importCheck = @"
import sys
try:
    import $pkg
    version_attr = getattr($pkg, '__version__', None)
    version = version_attr if version_attr else 'バージョン不明'
    print(f'✓ {pkg} ({version}) 正常にインポートされました')
except ImportError as e:
    print(f'✗ {pkg} がインストールされていないか問題があります: ' + str(e))
"@
        & poetry run python -c $importCheck
    }
    
    # 基本的なアプリケーションの起動確認
    Write-Host "`n== Application Startup Check ==" -ForegroundColor Green
    try {
        $appStartCheck = @"
import sys
try:
    from app.main import app
    print('✓ アプリケーションの起動確認に成功しました')
    print(f'✓ APIバージョン: {app.version}')
except Exception as e:
    print('✗ アプリケーションのインポートに失敗しました: ' + str(e))
"@
        & poetry run python -c $appStartCheck
    }
    catch {
        Write-Host "✗ アプリケーション起動チェックに失敗しました: $_" -ForegroundColor Red
    }
    
    Write-Host "`n== Network Check ==" -ForegroundColor Green
    # ポート8000が使用中かどうかを確認
    try {
        $portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($portCheck) {
            $process = Get-Process -Id $portCheck.OwningProcess -ErrorAction SilentlyContinue
            Write-Host "! ポート 8000 は現在使用中です。プロセス名: $($process.Name), PID: $($portCheck.OwningProcess)" -ForegroundColor Yellow
        }
        else {
            Write-Host "✓ ポート 8000 は利用可能です" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "! ポートチェックに失敗しました: $_" -ForegroundColor Yellow
    }
    
    Write-Host "`n-----------------------------------" -ForegroundColor Cyan
    Write-Host "環境検証が完了しました！" -ForegroundColor Green
} 
catch {
    Write-Host "`n-----------------------------------" -ForegroundColor Red
    Write-Host "環境検証中にエラーが発生しました: $_" -ForegroundColor Red
    exit 1
}
finally {
    # 元のディレクトリに戻る
    Pop-Location
}
