#!/usr/bin/env pwsh
# wrapper_run_app.ps1 - アプリケーション実行スクリプト（ラッパー）

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

Write-Host "=== KOIKI-FW アプリケーション実行 ===" -ForegroundColor Cyan
Write-Host "バージョン: 0.3.0" -ForegroundColor Cyan
Write-Host "開始時刻: $(Get-Date)" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# コマンドライン引数を渡して scripts/run_app.ps1 を呼び出す
try {
    # スクリプトのパスを取得
    $runAppScript = Join-Path $PSScriptRoot "scripts\run_app.ps1"
    
    # コマンドライン引数をそのまま scripts/run_app.ps1 に渡す
    & "$runAppScript" @args
    
    if ($LASTEXITCODE -ne 0) {
        throw "アプリケーション実行スクリプトが失敗しました。終了コード: $LASTEXITCODE"
    }
}
catch {
    Write-Host "エラーが発生しました：$_" -ForegroundColor Red
    exit 1
}