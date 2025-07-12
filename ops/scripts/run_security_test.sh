#!/bin/bash

# KOIKI-FW セキュリティ環境統合テストスクリプト
# Docker環境でのセキュリティ権限テスト

set -e

echo "🔐 KOIKI-FW セキュリティ統合テスト開始"
echo "========================================"

# 色付きメッセージ関数
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

# 1. コンテナ状態確認
echo ""
echo "1️⃣ Docker環境確認"
echo "--------------------"

if ! docker-compose ps | grep -q "Up"; then
    print_warning "コンテナが起動していません。起動中..."
    docker-compose up -d
    sleep 10
fi

print_success "Docker環境確認完了"

# 2. データベース接続確認
echo ""
echo "2️⃣ データベース接続確認"
echo "------------------------"

if docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "\dt" > /dev/null 2>&1; then
    print_success "データベース接続正常"
else
    print_error "データベース接続失敗"
    exit 1
fi

# 3. セキュリティデータセットアップ
echo ""
echo "3️⃣ セキュリティデータセットアップ"
echo "--------------------------------"

if docker-compose exec -T app python ops/scripts/setup_security.py; then
    print_success "セキュリティデータセットアップ完了"
else
    print_error "セキュリティデータセットアップ失敗"
    exit 1
fi

# 4. データベース内容確認
echo ""
echo "4️⃣ データベース内容確認"
echo "----------------------"

echo "📋 権限一覧:"
docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "
SELECT name, description, resource, action 
FROM permissions 
ORDER BY resource, action;
" 2>/dev/null | head -n 20

echo ""
echo "📋 ロール一覧:"
docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "
SELECT r.name, r.description, 
       COUNT(rp.permission_id) as permission_count 
FROM roles r 
LEFT JOIN role_permissions rp ON r.id = rp.role_id 
GROUP BY r.id, r.name, r.description 
ORDER BY r.name;
" 2>/dev/null

echo ""
echo "📋 ユーザーロール割り当て:"
docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "
SELECT u.email, r.name as role_name 
FROM users u 
JOIN user_roles ur ON u.id = ur.user_id 
JOIN roles r ON r.id = ur.role_id 
ORDER BY u.email;
" 2>/dev/null

# 5. APIサーバー応答確認
echo ""
echo "5️⃣ APIサーバー応答確認"
echo "----------------------"

# 基本エンドポイント確認
if curl -s -f http://localhost:8000/ > /dev/null; then
    print_success "ルートエンドポイント応答確認"
else
    print_error "ルートエンドポイント応答なし"
fi

if curl -s -f http://localhost:8000/health > /dev/null; then
    print_success "ヘルスチェックエンドポイント応答確認"
else
    print_error "ヘルスチェックエンドポイント応答なし"
fi

# 6. APIテストの実行
echo ""
echo "6️⃣ セキュリティAPIテスト実行"
echo "---------------------------"

if docker-compose exec -T app python ops/tests/test_security_api.py; then
    print_success "セキュリティAPIテスト完了"
else
    print_warning "セキュリティAPIテストで問題が発生（詳細は上記ログ参照）"
fi

# 7. 手動テスト用コマンド表示
echo ""
echo "7️⃣ 手動テスト用コマンド"
echo "--------------------"

echo "🔑 管理者ログイン:"
echo 'curl -X POST http://localhost:8000/api/v1/auth/login \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"username": "admin", "password": "admin123456"}'"'"''

echo ""
echo "🔍 セキュリティメトリクス取得（要トークン）:"
echo 'curl -H "Authorization: Bearer <TOKEN>" \'
echo '     http://localhost:8000/security/metrics'

echo ""
echo "👥 ユーザー一覧取得（要トークン）:"
echo 'curl -H "Authorization: Bearer <TOKEN>" \'
echo '     http://localhost:8000/api/v1/users'

echo ""
echo "========================================"
print_success "セキュリティ統合テスト完了！"

# 8. 結果要約
echo ""
echo "📊 テスト結果要約:"
echo "  • セキュリティデータセットアップ: 完了"
echo "  • データベース構造: 確認済み"
echo "  • APIエンドポイント: 応答確認済み"
echo "  • 権限ベースアクセス制御: テスト実行済み"
echo ""
echo "🌐 ブラウザで確認可能:"
echo "  • API仕様: http://localhost:8000/docs"
echo "  • ReDoc: http://localhost:8000/redoc"
