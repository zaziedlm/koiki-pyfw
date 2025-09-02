#!/bin/bash

# CSRF検証テストスクリプトの実行用シェルスクリプト

echo "🔐 CSRF検証テストスクリプト実行"
echo "================================"

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3が見つかりません"
    exit 1
fi

# 仮想環境がアクティブかチェック
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 仮想環境: $VIRTUAL_ENV"
else
    echo "⚠️ 仮想環境がアクティブではありません"
    echo "   以下のコマンドで仮想環境をアクティブにしてください:"
    echo "   source venv/bin/activate  # または適切な仮想環境のパス"
fi

echo ""
echo "📋 前提条件の確認:"
echo "  1. バックエンドサーバーが起動していること (python main.py)"
echo "  2. フロントエンドサーバーが起動していること (cd frontend && npm run dev)" 
echo "  3. テストユーザーが登録されていること (user@example.com / testuser123456)"
echo ""

read -p "準備ができましたか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "テストを中止しました"
    exit 0
fi

echo ""
echo "🚀 CSRFテスト実行中..."
echo ""

# CSRFテストスクリプトを実行
python3 ops/tests/test_csrf_validation.py

echo ""
echo "✅ CSRFテスト完了"
