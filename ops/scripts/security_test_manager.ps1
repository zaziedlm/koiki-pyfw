# KOIKI-FW セキュリティテスト管理スクリプト (PowerShell版)
# Cross-platform security test management for Windows

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# 色付きメッセージ関数
function Write-Header {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# ヘルプ表示
function Show-Help {
    Write-Header "KOIKI-FW セキュリティテスト用コマンド"
    Write-Header "===================================="
    Write-Host ""
    Write-Host "使用方法: .\security_test_manager.ps1 <command>"
    Write-Host ""
    Write-Host "利用可能なコマンド:"
    Write-Host "  help          このヘルプを表示"
    Write-Host "  setup         セキュリティ環境セットアップ"
    Write-Host "  test          セキュリティAPIテスト実行"
    Write-Host "  test-full     統合テスト実行"
    Write-Host "  clean         コンテナ停止"
    Write-Host "  reset         完全リセット（データ削除）"
    Write-Host "  logs          ログ確認"
    Write-Host "  db-check      データベース内容確認"
    Write-Host "  manual-test   手動テスト用情報表示"
    Write-Host ""
    Write-Host "例:"
    Write-Host "  .\security_test_manager.ps1 setup      # セキュリティ環境をセットアップ"
    Write-Host "  .\security_test_manager.ps1 test       # テストを実行"
    Write-Host ""
}

# Docker Composeコマンド実行関数
function Invoke-DockerCompose {
    param([string]$Arguments)
    
    try {
        $process = Start-Process -FilePath "docker-compose" -ArgumentList $Arguments -Wait -PassThru -NoNewWindow
        return $process.ExitCode -eq 0
    }
    catch {
        Write-Error "Docker Composeの実行に失敗しました: $_"
        return $false
    }
}

# セキュリティ環境セットアップ
function Setup-Security {
    Write-Info "🔐 セキュリティ環境セットアップ開始..."
    
    # Docker環境起動
    Write-Info "Docker環境起動中..."
    if (-not (Invoke-DockerCompose "up -d")) {
        Write-Error "Docker環境の起動に失敗しました"
        exit 1
    }
    
    # 少し待機
    Write-Info "アプリケーション起動待機中（5秒）..."
    Start-Sleep -Seconds 5
    
    # セキュリティデータ初期化
    Write-Info "セキュリティデータ初期化中..."
    if (Invoke-DockerCompose "exec app python ops/scripts/setup_security.py") {
        Write-Success "セキュリティ環境セットアップ完了！"
    }
    else {
        Write-Error "セキュリティデータ初期化に失敗しました"
        exit 1
    }
}

# セキュリティAPIテスト実行
function Start-Test {
    Write-Info "🧪 セキュリティAPIテスト実行..."
    
    if (Invoke-DockerCompose "exec app python ops/tests/test_security_api.py") {
        Write-Success "セキュリティAPIテスト完了！"
    }
    else {
        Write-Warning "テストで問題が発生しました（詳細は上記ログ参照）"
    }
}

# 統合テスト実行
function Start-FullTest {
    Write-Info "🔄 統合テスト実行..."
    
    # PowerShell版では統合テストスクリプトを直接実行
    $shellScript = "ops\scripts\run_security_test.sh"
    if (Test-Path $shellScript) {
        # WSL または Git Bash での実行を試行
        try {
            if (Get-Command wsl -ErrorAction SilentlyContinue) {
                Write-Info "WSLで統合テストを実行中..."
                wsl bash $shellScript
            }
            elseif (Get-Command bash -ErrorAction SilentlyContinue) {
                Write-Info "Git Bashで統合テストを実行中..."
                bash $shellScript
            }
            else {
                Write-Warning "Bashが利用できません。個別テストを実行します..."
                Start-Test
            }
        }
        catch {
            Write-Warning "統合テストスクリプトの実行に失敗しました。個別テストを実行します..."
            Start-Test
        }
    }
    else {
        Write-Error "統合テストスクリプトが見つかりません"
        exit 1
    }
}

# 環境クリーンアップ
function Clear-Environment {
    Write-Info "🧹 環境クリーンアップ..."
    if (Invoke-DockerCompose "down") {
        Write-Success "クリーンアップ完了"
    }
    else {
        Write-Error "クリーンアップに失敗しました"
    }
}

# 完全リセット
function Reset-Environment {
    Write-Warning "🔄 完全リセット実行中..."
    Write-Warning "⚠️  データベースのデータも削除されます"
    
    # 確認プロンプト
    $confirm = Read-Host "続行しますか? (y/N)"
    if ($confirm -notmatch "^[Yy]$") {
        Write-Info "キャンセルされました"
        exit 0
    }
    
    Invoke-DockerCompose "down -v"
    Write-Info "コンテナ再ビルド中..."
    Invoke-DockerCompose "up --build -d"
    
    Write-Info "アプリケーション起動待機中（10秒）..."
    Start-Sleep -Seconds 10
    
    Write-Info "セキュリティデータ再初期化中..."
    Invoke-DockerCompose "exec app python ops/scripts/setup_security.py"
    
    Write-Success "完全リセット完了！"
}

# ログ確認
function Show-Logs {
    Write-Info "📋 アプリケーションログを表示中..."
    Write-Info "（Ctrl+C で終了）"
    docker-compose logs -f app
}

# データベース内容確認
function Test-Database {
    Write-Info "📊 データベース内容確認..."
    
    Write-Host ""
    Write-Header "権限一覧:"
    try {
        docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT name, resource, action, description FROM koiki_permissions ORDER BY resource, action;" 2>$null
    }
    catch {
        Write-Error "権限テーブルにアクセスできません"
    }
    
    Write-Host ""
    Write-Header "ロール一覧:"
    try {
        docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT r.name as role_name, r.description, COUNT(rp.permission_id) as permission_count FROM koiki_roles r LEFT JOIN koiki_role_permissions rp ON r.id = rp.role_id GROUP BY r.id, r.name, r.description ORDER BY r.name;" 2>$null
    }
    catch {
        Write-Error "ロールテーブルにアクセスできません"
    }
    
    Write-Host ""
    Write-Header "ユーザーロール割り当て:"
    try {
        docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT u.email, u.username, r.name as role_name FROM koiki_users u JOIN koiki_user_roles ur ON u.id = ur.user_id JOIN koiki_roles r ON r.id = ur.role_id ORDER BY u.email;" 2>$null
    }
    catch {
        Write-Error "ユーザーテーブルにアクセスできません"
    }
}

# 手動テスト用情報表示
function Show-ManualTestInfo {
    Write-Header "🔑 手動テスト用コマンド"
    Write-Header "======================"
    Write-Host ""
    
    Write-Info "1. 管理者ログイン:"
    Write-Host 'curl -X POST http://localhost:8000/api/v1/auth/login \'
    Write-Host '  -H "Content-Type: application/json" \'
    Write-Host '  -d ''{"username": "admin", "password": "admin123456"}'''
    Write-Host ""
    
    Write-Info "2. セキュリティメトリクス取得:"
    Write-Host 'curl -H "Authorization: Bearer <TOKEN>" \'
    Write-Host '     http://localhost:8000/security/metrics'
    Write-Host ""
    
    Write-Info "3. ユーザー一覧取得:"
    Write-Host 'curl -H "Authorization: Bearer <TOKEN>" \'
    Write-Host '     http://localhost:8000/api/v1/users'
    Write-Host ""
    
    Write-Info "4. 権限テスト（一般ユーザーで403エラー確認）:"
    Write-Host 'curl -X POST http://localhost:8000/api/v1/auth/login \'
    Write-Host '  -H "Content-Type: application/json" \'
    Write-Host '  -d ''{"username": "testuser", "password": "testuser123456"}'''
    Write-Host ""
    Write-Host 'curl -H "Authorization: Bearer <TESTUSER_TOKEN>" \'
    Write-Host '     http://localhost:8000/security/metrics'
    Write-Host ""
    
    Write-Header "📋 テストユーザー:"
    Write-Host "  • admin@example.com / admin123456 (system_admin)"
    Write-Host "  • security@example.com / security123456 (security_admin)"
    Write-Host "  • user_admin@example.com / useradmin123456 (user_admin)"
    Write-Host "  • user@example.com / testuser123456 (todo_user)"
    Write-Host ""
    
    Write-Header "🌐 ブラウザアクセス:"
    Write-Host "  • API仕様: http://localhost:8000/docs"
    Write-Host "  • ReDoc: http://localhost:8000/redoc"
    Write-Host "  • ヘルスチェック: http://localhost:8000/health"
}

# メイン処理
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Setup-Security }
    "test" { Start-Test }
    "test-full" { Start-FullTest }
    "clean" { Clear-Environment }
    "reset" { Reset-Environment }
    "logs" { Show-Logs }
    "db-check" { Test-Database }
    "manual-test" { Show-ManualTestInfo }
    default {
        Write-Error "不明なコマンド: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}
