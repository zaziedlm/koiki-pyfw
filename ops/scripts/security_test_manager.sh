#!/bin/bash

# KOIKI-FW セキュリティテスト管理スクリプト
# Cross-platform security test management

set -e

# 色付きメッセージ関数
print_header() {
    echo -e "\033[36m$1\033[0m"
}

print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

print_info() {
    echo -e "\033[34mℹ️  $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

# ヘルプ表示
show_help() {
    print_header "KOIKI-FW セキュリティテスト用コマンド"
    print_header "===================================="
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "利用可能なコマンド:"
    echo "  help          このヘルプを表示"
    echo "  setup         セキュリティ環境セットアップ"
    echo "  test          セキュリティAPIテスト実行"
    echo "  test-full     統合テスト実行"
    echo "  clean         コンテナ停止"
    echo "  reset         完全リセット（データ削除）"
    echo "  logs          ログ確認"
    echo "  db-check      データベース内容確認"
    echo "  manual-test   手動テスト用情報表示"
    echo ""
    echo "例:"
    echo "  $0 setup      # セキュリティ環境をセットアップ"
    echo "  $0 test       # テストを実行"
    echo ""
}

# セキュリティ環境セットアップ
setup_security() {
    print_info "🔐 セキュリティ環境セットアップ開始..."
    
    # Docker環境起動
    print_info "Docker環境起動中..."
    docker-compose up -d
    
    # 少し待機
    print_info "アプリケーション起動待機中（5秒）..."
    sleep 5
    
    # セキュリティデータ初期化
    print_info "セキュリティデータ初期化中..."
    if docker-compose exec app python ops/scripts/setup_security.py; then
        print_success "セキュリティ環境セットアップ完了！"
    else
        print_error "セキュリティデータ初期化に失敗しました"
        exit 1
    fi
}

# セキュリティAPIテスト実行
run_test() {
    print_info "🧪 セキュリティAPIテスト実行..."
    
    if docker-compose exec app python ops/tests/test_security_api.py; then
        print_success "セキュリティAPIテスト完了！"
    else
        print_warning "テストで問題が発生しました（詳細は上記ログ参照）"
    fi
}

# 統合テスト実行
run_full_test() {
    print_info "🔄 統合テスト実行..."
    
    if [ -f "ops/scripts/run_security_test.sh" ]; then
        chmod +x ops/scripts/run_security_test.sh
        ./ops/scripts/run_security_test.sh
    else
        print_error "統合テストスクリプトが見つかりません"
        exit 1
    fi
}

# 環境クリーンアップ
clean_environment() {
    print_info "🧹 環境クリーンアップ..."
    docker-compose down
    print_success "クリーンアップ完了"
}

# 完全リセット
reset_environment() {
    print_warning "🔄 完全リセット実行中..."
    print_warning "⚠️  データベースのデータも削除されます"
    
    # 確認プロンプト
    read -p "続行しますか? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "キャンセルされました"
        exit 0
    fi
    
    docker-compose down -v
    print_info "コンテナ再ビルド中..."
    docker-compose up --build -d
    
    print_info "アプリケーション起動待機中（10秒）..."
    sleep 10
    
    print_info "セキュリティデータ再初期化中..."
    docker-compose exec app python ops/scripts/setup_security.py
    
    print_success "完全リセット完了！"
}

# ログ確認
show_logs() {
    print_info "📋 アプリケーションログを表示中..."
    print_info "（Ctrl+C で終了）"
    docker-compose logs -f app
}

# データベース内容確認
check_database() {
    print_info "📊 データベース内容確認..."
    
    echo ""
    print_header "権限一覧:"
    docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "
        SELECT name, resource, action, description 
        FROM permissions 
        ORDER BY resource, action;
    " 2>/dev/null || print_error "権限テーブルにアクセスできません"
    
    echo ""
    print_header "ロール一覧:"
    docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "
        SELECT r.name as role_name, r.description, 
               COUNT(rp.permission_id) as permission_count
        FROM roles r 
        LEFT JOIN role_permissions rp ON r.id = rp.role_id 
        GROUP BY r.id, r.name, r.description 
        ORDER BY r.name;
    " 2>/dev/null || print_error "ロールテーブルにアクセスできません"
    
    echo ""
    print_header "ユーザーロール割り当て:"
    docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "
        SELECT u.email, u.username, r.name as role_name
        FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        JOIN roles r ON r.id = ur.role_id 
        ORDER BY u.email;
    " 2>/dev/null || print_error "ユーザーテーブルにアクセスできません"
}

# 手動テスト用情報表示
show_manual_test_info() {
    print_header "🔑 手動テスト用コマンド"
    print_header "======================"
    echo ""
    
    print_info "1. 管理者ログイン:"
    echo 'curl -X POST http://localhost:8000/api/v1/auth/login \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"username": "admin", "password": "admin123456"}'"'"''
    echo ""
    
    print_info "2. セキュリティメトリクス取得:"
    echo 'curl -H "Authorization: Bearer <TOKEN>" \'
    echo '     http://localhost:8000/security/metrics'
    echo ""
    
    print_info "3. ユーザー一覧取得:"
    echo 'curl -H "Authorization: Bearer <TOKEN>" \'
    echo '     http://localhost:8000/api/v1/users'
    echo ""
    
    print_info "4. 権限テスト（一般ユーザーで403エラー確認）:"
    echo 'curl -X POST http://localhost:8000/api/v1/auth/login \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"username": "testuser", "password": "testuser123456"}'"'"''
    echo ""
    echo 'curl -H "Authorization: Bearer <TESTUSER_TOKEN>" \'
    echo '     http://localhost:8000/security/metrics'
    echo ""
    
    print_header "📋 テストユーザー:"
    echo "  • admin@example.com / admin123456 (system_admin)"
    echo "  • security@example.com / security123456 (security_admin)"
    echo "  • user_admin@example.com / useradmin123456 (user_admin)"
    echo "  • user@example.com / testuser123456 (todo_user)"
    echo ""
    
    print_header "🌐 ブラウザアクセス:"
    echo "  • API仕様: http://localhost:8000/docs"
    echo "  • ReDoc: http://localhost:8000/redoc"
    echo "  • ヘルスチェック: http://localhost:8000/health"
}

# メイン処理
main() {
    case "${1:-help}" in
        help)
            show_help
            ;;
        setup)
            setup_security
            ;;
        test)
            run_test
            ;;
        test-full)
            run_full_test
            ;;
        clean)
            clean_environment
            ;;
        reset)
            reset_environment
            ;;
        logs)
            show_logs
            ;;
        db-check)
            check_database
            ;;
        manual-test)
            show_manual_test_info
            ;;
        *)
            print_error "不明なコマンド: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"
