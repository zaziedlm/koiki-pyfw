#!/usr/bin/env pwsh
# wrapper_init_env.ps1 - 開発環境初期化スクリプト（ラッパー）

# エラーの詳細な出力を有効化
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

Write-Host "=== KOIKI-FW 開発環境初期化 ===" -ForegroundColor Cyan
Write-Host "バージョン: 0.3.0" -ForegroundColor Cyan
Write-Host "開始時刻: $(Get-Date)" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

try {
    # scripts/init_poetry_env.ps1を呼び出す
    Write-Host "Poetryを使用して開発環境を初期化しています..." -ForegroundColor Green
    & "$PSScriptRoot\scripts\init_poetry_env.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        throw "環境初期化スクリプトが失敗しました。終了コード: $LASTEXITCODE"
    }
    
    Write-Host "-----------------------------------" -ForegroundColor Cyan
    Write-Host "環境初期化が完了しました！" -ForegroundColor Green
    Write-Host "次のステップ：" -ForegroundColor Cyan
    Write-Host "  1. 'wrapper_run_app.ps1' を実行してアプリケーションを起動" -ForegroundColor Cyan
    Write-Host "  2. ブラウザで 'http://localhost:8000/docs' にアクセス" -ForegroundColor Cyan
}
catch {
    Write-Host "-----------------------------------" -ForegroundColor Red
    Write-Host "エラーが発生しました：$_" -ForegroundColor Red
    Write-Host "環境初期化に失敗しました。" -ForegroundColor Red
    exit 1
}
