#!/bin/bash

# KOIKI-FW セキュリティテスト実行スクリプト
# Usage: ./run_security_test.sh [command]

set -e

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 KOIKI-FW セキュリティテスト実行${NC}"
echo "=================================================="

# Docker環境確認
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose がインストールされていません${NC}"
    exit 1
fi

# プロジェクトルートディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# コマンド処理
COMMAND=${1:-"test"}

case $COMMAND in
    "start"|"up")
        echo -e "${YELLOW}🚀 Docker環境を起動中...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ Docker環境が起動しました${NC}"
        ;;
    "setup")
        echo -e "${YELLOW}🔧 セキュリティ環境をセットアップ中...${NC}"
        docker-compose up -d
        cd ops && bash scripts/security_test_manager.sh setup
        echo -e "${GREEN}✅ セキュリティ環境のセットアップが完了しました${NC}"
        ;;
    "test")
        echo -e "${YELLOW}🧪 セキュリティテストを実行中...${NC}"
        docker-compose up -d
        cd ops && bash scripts/security_test_manager.sh test
        ;;
    "test-full")
        echo -e "${YELLOW}🔬 統合テストを実行中...${NC}"
        docker-compose up -d
        cd ops && bash scripts/security_test_manager.sh test-full
        ;;
    "stop"|"down")
        echo -e "${YELLOW}🛑 Docker環境を停止中...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Docker環境を停止しました${NC}"
        ;;
    "reset")
        echo -e "${YELLOW}🔄 環境をリセット中...${NC}"
        docker-compose down -v
        docker-compose up -d
        cd ops && bash scripts/security_test_manager.sh setup
        echo -e "${GREEN}✅ 環境のリセットが完了しました${NC}"
        ;;
    "logs")
        echo -e "${YELLOW}📋 ログを表示中...${NC}"
        docker-compose logs -f app
        ;;
    "help"|"-h"|"--help")
        echo -e "${BLUE}利用可能なコマンド:${NC}"
        echo "  start     Docker環境を起動"
        echo "  setup     セキュリティ環境をセットアップ"
        echo "  test      セキュリティテストを実行（デフォルト）"
        echo "  test-full 統合テストを実行"
        echo "  stop      Docker環境を停止"
        echo "  reset     環境を完全リセット"
        echo "  logs      アプリケーションログを表示"
        echo "  help      このヘルプを表示"
        echo ""
        echo -e "${BLUE}使用例:${NC}"
        echo "  ./run_security_test.sh           # テスト実行"
        echo "  ./run_security_test.sh setup     # セットアップ"
        echo "  ./run_security_test.sh test-full # 統合テスト"
        ;;
    *)
        echo -e "${RED}❌ 不明なコマンド: $COMMAND${NC}"
        echo "利用可能なコマンドを確認するには: ./run_security_test.sh help"
        exit 1
        ;;
esac

echo -e "${GREEN}🎉 完了！${NC}"
