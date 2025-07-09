# KOIKI Framework - ローカル開発用起動スクリプト
# 使用方法: .\start-local-dev.ps1

Write-Host "KOIKI Framework - ローカル開発環境起動中..." -ForegroundColor Green

# 1. データベースコンテナが起動していることを確認
Write-Host "データベースコンテナの状態を確認中..." -ForegroundColor Yellow
$dbStatus = docker-compose ps -q db
if (-not $dbStatus) {
    Write-Host "データベースコンテナを起動中..." -ForegroundColor Yellow
    docker-compose up -d db
    
    # データベースの準備完了を待つ
    Write-Host "データベースの準備完了を待機中..." -ForegroundColor Yellow
    do {
        Start-Sleep -Seconds 2
        $healthStatus = docker-compose ps --format "json" | ConvertFrom-Json | Where-Object { $_.Name -like "*postgres*" } | Select-Object -First 1
        Write-Host "." -NoNewline
    } while ($healthStatus.Status -notlike "*healthy*")
    
    Write-Host "`nデータベースの準備が完了しました。" -ForegroundColor Green
}

# 2. ローカル環境変数を設定
Write-Host "ローカル環境変数を設定中..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db"
$env:POSTGRES_SERVER = "localhost"
$env:APP_ENV = "development"
$env:DEBUG = "True"

# 3. Alembicでマイグレーションを実行
Write-Host "データベースマイグレーションを実行中..." -ForegroundColor Yellow
alembic upgrade head

# 4. アプリケーションを起動
Write-Host "KOIKIフレームワークアプリケーションを起動中..." -ForegroundColor Green
Write-Host "アクセスURL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API ドキュメント: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "停止するには Ctrl+C を押してください" -ForegroundColor Yellow

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
