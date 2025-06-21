# 企業向けセキュリティ監査コマンド

## 依存性脆弱性スキャン

### 1. 基本的なセキュリティチェック

```bash
# セキュリティツールのインストール
poetry install --with security

# Safety - 既知の脆弱性データベースチェック
poetry run safety check

# pip-audit - OSV データベース監査
poetry run pip-audit

# Bandit - Pythonコードの静的セキュリティ解析
poetry run bandit -r . -f json -o security-report.json
poetry run bandit -r . --severity-level medium
```

### 2. 継続的セキュリティ監視

```bash
# 日次セキュリティチェック
#!/bin/bash
echo "=== Daily Security Audit ==="
echo "Date: $(date)"
echo ""

echo "1. Dependency Vulnerability Scan (Safety):"
poetry run safety check --json > safety-report-$(date +%Y%m%d).json
poetry run safety check

echo ""
echo "2. OSV Database Audit (pip-audit):"
poetry run pip-audit --format=json --output=audit-report-$(date +%Y%m%d).json
poetry run pip-audit

echo ""
echo "3. Static Code Security Analysis (Bandit):"
poetry run bandit -r . -f json -o bandit-report-$(date +%Y%m%d).json
poetry run bandit -r . --severity-level low

echo ""
echo "4. Outdated Dependencies Check:"
poetry show --outdated

echo "=== Security Audit Complete ==="
```

### 3. 緊急セキュリティアップデート

```bash
# 緊急CVE対応プロセス
echo "=== Emergency Security Update Process ==="

# 1. 現在のバージョン確認
poetry show | grep -E "(fastapi|uvicorn|sqlalchemy|pydantic)"

# 2. 脆弱性影響確認
poetry run safety check --json | jq '.vulnerabilities[]'

# 3. 特定パッケージの緊急更新
poetry add "fastapi>=0.104.2,<0.105.0"  # 例: セキュリティ修正版
poetry add "pydantic>=2.5.1,<2.6.0"     # 例: セキュリティ修正版

# 4. 依存性整合性確認
poetry check --lock
poetry lock
poetry install

# 5. セキュリティ再検証
poetry run safety check
poetry run pip-audit

# 6. テスト実行
poetry run pytest tests/

echo "=== Emergency Update Complete ==="
```

## 本番環境デプロイ前チェックリスト

### セキュリティ検証プロセス

```bash
#!/bin/bash
# pre-deploy-security-check.sh

set -e

echo "🔒 Pre-deployment Security Verification"
echo "======================================="

# 1. 依存性脆弱性スキャン
echo "1. Vulnerability Scanning..."
poetry run safety check --json > pre-deploy-safety.json
if ! poetry run safety check; then
    echo "❌ Vulnerability found! Deployment blocked."
    exit 1
fi

# 2. 依存性監査
echo "2. Dependency Audit..."
poetry run pip-audit --format=json --output=pre-deploy-audit.json
if ! poetry run pip-audit; then
    echo "❌ Audit failed! Deployment blocked."
    exit 1
fi

# 3. コードセキュリティ解析
echo "3. Static Security Analysis..."
poetry run bandit -r . -f json -o pre-deploy-bandit.json
if ! poetry run bandit -r . --severity-level medium; then
    echo "⚠️  Security issues found. Review required."
    # 注意: 中レベル以上のセキュリティ問題がある場合は要レビュー
fi

# 4. 設定ファイル検証
echo "4. Configuration Security Check..."
if grep -r "password\|secret\|key" . --exclude-dir=.git --exclude-dir=.venv --exclude="*.md"; then
    echo "⚠️  Potential secrets in code. Manual review required."
fi

# 5. Dockerセキュリティ
echo "5. Container Security Baseline..."
docker run --rm -v "$(pwd)":/app hadolint/hadolint hadolint /app/Dockerfile

echo "✅ Security verification complete!"
echo "📄 Reports generated:"
echo "   - pre-deploy-safety.json"
echo "   - pre-deploy-audit.json" 
echo "   - pre-deploy-bandit.json"
```

## 月次セキュリティレビュー

```bash
#!/bin/bash
# monthly-security-review.sh

echo "📅 Monthly Security Review - $(date +%Y-%m)"
echo "============================================"

# 1. 全依存性の最新状況確認
echo "1. Dependency Status Review:"
poetry show --outdated > monthly-outdated-$(date +%Y%m).txt
poetry show --tree > monthly-deps-tree-$(date +%Y%m).txt

# 2. 累積脆弱性レポート
echo "2. Cumulative Vulnerability Report:"
poetry run safety check --json > monthly-safety-$(date +%Y%m).json

# 3. セキュリティ設定レビュー
echo "3. Security Configuration Review:"
echo "   - Environment variables check"
echo "   - CORS settings verification"
echo "   - Rate limiting configuration"
echo "   - Authentication mechanisms"

# 4. Docker セキュリティベースライン
echo "4. Container Security Assessment:"
docker scout cves local://koiki-pyfw-app > monthly-docker-cves-$(date +%Y%m).txt

# 5. 推奨アクション生成
echo "5. Recommended Actions:"
echo "   See generated reports for specific recommendations"

echo "📊 Monthly review complete. Reports saved with timestamp."
```

## エンタープライズ監査統合

### CI/CD パイプライン統合

```yaml
# .github/workflows/security-audit.yml
name: Security Audit

on:
  schedule:
    - cron: '0 2 * * *'  # 毎日午前2時
  pull_request:
    branches: [ master, develop ]

jobs:
  security-audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11.7'
    
    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 - --version 2.1.0
        echo "$HOME/.local/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: |
        poetry install --with security
    
    - name: Run Safety Check
      run: |
        poetry run safety check --json --output safety-report.json
        poetry run safety check
    
    - name: Run pip-audit
      run: |
        poetry run pip-audit --format=json --output audit-report.json
    
    - name: Run Bandit
      run: |
        poetry run bandit -r . -f json -o bandit-report.json
        poetry run bandit -r . --severity-level medium
    
    - name: Upload Security Reports
      uses: actions/upload-artifact@v4
      with:
        name: security-reports
        path: |
          safety-report.json
          audit-report.json
          bandit-report.json
```