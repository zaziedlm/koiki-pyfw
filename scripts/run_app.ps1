#!/usr/bin/env pwsh
# run_app.ps1 - KOIKI-FWアプリケーション実行スクリプト

param (
    [string]$HostName = "127.0.0.1",  # $Host は予約語なので $HostName に変更
    [int]$Port = 8000,
    [switch]$Production
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

Write-Host "=== KOIKI-FW アプリケーション実行 ===" -ForegroundColor Cyan
Write-Host "バージョン: 0.3.0" -ForegroundColor Cyan
Write-Host "開始時刻: $(Get-Date)" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# プロジェクトルートディレクトリのパスを取得
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $scriptDir

# プロジェクトルートディレクトリに移動
Write-Host "アプリケーションディレクトリ: $rootDir" -ForegroundColor Cyan
Push-Location $rootDir

# ポート8000が使用中かチェック
try {
    $portCheck = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($portCheck) {
        $process = Get-Process -Id $portCheck.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "警告: ポート $Port は既に使用されています。プロセス名: $($process.Name), PID: $($portCheck.OwningProcess)" -ForegroundColor Yellow
        $confirmation = Read-Host "プロセスを終了してアプリケーションを起動しますか？(Y/n)"
        if ($confirmation -eq "" -or $confirmation -eq "Y" -or $confirmation -eq "y") {
            try {
                Stop-Process -Id $portCheck.OwningProcess -Force
                Write-Host "プロセスを終了しました。" -ForegroundColor Green
                # プロセスが終了するまで少し待機
                Start-Sleep -Seconds 1
            }
            catch {
                Write-Host "プロセスの終了に失敗しました: $_" -ForegroundColor Red
                exit 1
            }
        }
        else {
            Write-Host "アプリケーションの起動を中止します。" -ForegroundColor Red
            exit 1
        }
    }
}
catch {
    # ポートチェックに失敗しても続行
    Write-Host "ポートチェックに失敗しました: $_" -ForegroundColor Yellow
}

try {
    # アプリケーションの起動
    Write-Host "Starting application with Uvicorn on ${HostName}:${Port}..." -ForegroundColor Green
    
    if ($Production) {
        # 本番環境用設定
        Write-Host "Running in PRODUCTION mode" -ForegroundColor Yellow
        & poetry run uvicorn app.main:app --host $HostName --port $Port --workers 4
    }
    else {
        # 開発環境用設定（リロード有効）
        Write-Host "Running in DEVELOPMENT mode with auto-reload" -ForegroundColor Green
        & poetry run uvicorn app.main:app --host $HostName --port $Port --reload
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Uvicorn failed to start. Exit code: $LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
} 
catch {
    Write-Host "アプリケーション実行中にエラーが発生しました: $_" -ForegroundColor Red
    exit 1
}
finally {
    # 元のディレクトリに戻る
    Pop-Location
}