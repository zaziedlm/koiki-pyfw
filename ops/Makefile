# KOIKI-FW セキュリティテスト用 Makefile (廃止予定)
# 
# 注意: このMakefileは廃止予定です
# Windows環境との互換性のため、以下のスクリプトを使用してください：
#
# 推奨方法:
#   ./ops/scripts/run_tests.sh <command>    # クロスプラットフォーム対応
#
# 環境別:
#   ./ops/scripts/security_test_manager.sh  # Unix系 (Bash)
#   ./ops/scripts/security_test_manager.ps1 # Windows (PowerShell)

.PHONY: help setup test clean reset logs migration-notice

migration-notice: ## 移行案内を表示
	@echo "⚠️  Makefileは廃止予定です"
	@echo "Windows環境との互換性のため、以下のスクリプトを使用してください："
	@echo ""
	@echo "推奨方法（全環境）:"
	@echo "  ./ops/scripts/run_tests.sh setup    # セットアップ"
	@echo "  ./ops/scripts/run_tests.sh test     # テスト実行"
	@echo "  ./ops/scripts/run_tests.sh help     # ヘルプ"
	@echo ""
	@echo "環境別スクリプト:"
	@echo "  ./ops/scripts/security_test_manager.sh   # Unix系"
	@echo "  ./ops/scripts/security_test_manager.ps1  # Windows"

help: migration-notice ## ヘルプを表示（移行案内付き）
	@echo "KOIKI-FW セキュリティテスト用コマンド"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: migration-notice ## セキュリティ環境セットアップ（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh setup"
	@echo "🔐 セキュリティ環境セットアップ開始..."
	docker-compose up -d
	@sleep 5
	docker-compose exec app python ops/scripts/setup_security.py

test: migration-notice ## セキュリティAPIテスト実行（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh test"
	@echo "🧪 セキュリティAPIテスト実行..."
	docker-compose exec app python ops/tests/test_security_api.py

test-full: migration-notice ## 統合テスト実行（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh test-full"
	@echo "🔄 統合テスト実行..."
	./ops/scripts/run_security_test.sh

clean: migration-notice ## コンテナ停止（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh clean"
	@echo "🧹 環境クリーンアップ..."
	docker-compose down

reset: migration-notice ## 完全リセット（データ削除）（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh reset"
	@echo "🔄 完全リセット..."
	docker-compose down -v
	docker-compose up --build -d
	@sleep 10
	docker-compose exec app python ops/scripts/setup_security.py

logs: migration-notice ## ログ確認（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh logs"
	docker-compose logs -f app

db-check: migration-notice ## データベース内容確認（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh db-check"
	@echo "📊 データベース内容確認..."
	@echo "権限一覧:"
	@docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT name, resource, action FROM permissions ORDER BY resource, action;" 2>/dev/null || true
	@echo ""
	@echo "ユーザーロール:"
	@docker-compose exec -T db psql -U koiki_user -d koiki_todo_db -c "SELECT u.email, r.name FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON r.id = ur.role_id ORDER BY u.email;" 2>/dev/null || true

manual-test: migration-notice ## 手動テスト用情報表示（非推奨）
	@echo "⚠️  推奨: ./ops/scripts/run_tests.sh manual-test"
	@echo "🔑 手動テスト用コマンド"
	@echo "======================"
	@echo ""
	@echo "1. 管理者ログイン:"
	@echo "curl -X POST http://localhost:8000/api/v1/auth/login \\"
	@echo "  -H \"Content-Type: application/json\" \\"
	@echo "  -d '{\"username\": \"admin\", \"password\": \"admin123456\"}'"
	@echo ""
	@echo "2. セキュリティメトリクス取得:"
	@echo "curl -H \"Authorization: Bearer <TOKEN>\" \\"
	@echo "     http://localhost:8000/security/metrics"
	@echo ""
	@echo "3. ユーザー一覧取得:"
	@echo "curl -H \"Authorization: Bearer <TOKEN>\" \\"
	@echo "     http://localhost:8000/api/v1/users"
