#!/bin/bash
# verify-frontend-unified.sh
# frontend/Dockerfile.unifiedの動作検証スクリプト

set -e

echo "=========================================="
echo "Frontend Dockerfile.unified 検証スクリプト"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Change to frontend directory
cd frontend

echo "=========================================="
echo "1. 開発環境ビルド (dev target)"
echo "=========================================="
print_info "Building dev target..."
if time docker build \
    --file Dockerfile.unified \
    --target dev \
    --tag koiki-pyfw-frontend:dev-unified \
    . ; then
    print_success "開発環境ビルド成功"
else
    print_error "開発環境ビルド失敗"
    exit 1
fi
echo ""

echo "=========================================="
echo "2. 本番環境ビルド (runner target)"
echo "=========================================="
print_info "Building runner target..."
if time docker build \
    --file Dockerfile.unified \
    --target runner \
    --tag koiki-pyfw-frontend:runner-unified \
    . ; then
    print_success "本番環境ビルド成功"
else
    print_error "本番環境ビルド失敗"
    exit 1
fi
echo ""

echo "=========================================="
echo "3. イメージサイズ比較"
echo "=========================================="
print_info "既存Dockerfileとの比較..."
echo ""
echo "【統一Dockerfile】"
docker images | grep "koiki-pyfw-frontend.*unified" || echo "統一版イメージが見つかりません"
echo ""
echo "【既存Dockerfile】"
docker images | grep "koiki-pyfw-frontend" | grep -v "unified" || echo "既存イメージが見つかりません"
echo ""

echo "=========================================="
echo "4. キャッシュ効果確認（2回目ビルド）"
echo "=========================================="
print_info "2回目のrunner targetビルド..."
if time docker build \
    --file Dockerfile.unified \
    --target runner \
    --tag koiki-pyfw-frontend:runner-unified-cache-test \
    . ; then
    print_success "キャッシュ効果確認成功（上記の時間を1回目と比較）"
else
    print_error "2回目ビルド失敗"
    exit 1
fi
echo ""

echo "=========================================="
echo "5. ビルド検証完了"
echo "=========================================="
print_success "全てのビルドが正常に完了しました"
echo ""
echo "次のステップ:"
echo "  - docker-compose.dev-unified.yml でdev targetを使用して起動確認"
echo "  - docker-compose でrunner targetを使用して起動確認"
echo ""
