#!/bin/bash

# KOIKI-FW クロスプラットフォーム実行ランチャー
# Windows/Linux/macOS対応の統一インターフェース

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# OS検出
detect_os() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# PowerShell実行可能性チェック
check_powershell() {
    if command -v pwsh >/dev/null 2>&1; then
        echo "pwsh"
    elif command -v powershell >/dev/null 2>&1; then
        echo "powershell"
    else
        echo ""
    fi
}

# メイン実行ロジック
main() {
    local os_type=$(detect_os)
    local powershell_cmd=$(check_powershell)
    
    echo "🔍 OS検出: $os_type"
    
    # Windows環境での実行
    if [[ "$os_type" == "windows" ]] && [[ -n "$powershell_cmd" ]]; then
        echo "🖥️  PowerShellスクリプトを実行します..."
        cd "$PROJECT_ROOT"
        "$powershell_cmd" -ExecutionPolicy Bypass -File "ops/scripts/security_test_manager.ps1" "$@"
    # Unix系環境での実行
    elif [[ "$os_type" == "macos" ]] || [[ "$os_type" == "linux" ]]; then
        echo "🐧 Bashスクリプトを実行します..."
        cd "$PROJECT_ROOT"
        bash "ops/scripts/security_test_manager.sh" "$@"
    # PowerShellが利用可能な場合（Windows Subsystem for Linux等）
    elif [[ -n "$powershell_cmd" ]]; then
        echo "⚡ PowerShellスクリプトを実行します..."
        cd "$PROJECT_ROOT"
        "$powershell_cmd" -ExecutionPolicy Bypass -File "ops/scripts/security_test_manager.ps1" "$@"
    # フォールバック（Bashスクリプト）
    else
        echo "🔧 Bashスクリプトを実行します（フォールバック）..."
        cd "$PROJECT_ROOT"
        bash "ops/scripts/security_test_manager.sh" "$@"
    fi
}

# ヘルプ表示
show_launcher_help() {
    echo "🚀 KOIKI-FW クロスプラットフォーム実行ランチャー"
    echo "=============================================="
    echo ""
    echo "このランチャーは、OS環境に応じて適切なスクリプトを自動選択します："
    echo "  • Windows: PowerShellスクリプト (.ps1)"
    echo "  • macOS/Linux: Bashスクリプト (.sh)"
    echo ""
    echo "使用方法: $0 <command> [options]"
    echo ""
    echo "利用可能なコマンド:"
    echo "  help, setup, test, test-full, clean, reset, logs, db-check, manual-test"
    echo ""
    echo "例:"
    echo "  $0 setup      # セキュリティ環境をセットアップ"
    echo "  $0 test       # テストを実行"
    echo ""
    echo "環境固有のスクリプトを直接実行する場合:"
    echo "  • Bash: ./ops/scripts/security_test_manager.sh <command>"
    echo "  • PowerShell: ./ops/scripts/security_test_manager.ps1 <command>"
    echo ""
}

# 引数チェック
if [[ "${1:-help}" == "help" ]] && [[ $# -eq 1 ]]; then
    show_launcher_help
else
    main "$@"
fi
