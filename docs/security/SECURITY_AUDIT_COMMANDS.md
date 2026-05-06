# 企業向けセキュリティ監査コマンド

## 現行標準

- 依存同期: `uv sync --locked --group security`
- 依存性脆弱性監査: `uv run --locked pip-audit`
- 静的セキュリティ解析: `uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src`
- lockfile 正本: `uv.lock`

`safety` は現行の `security` dependency group には含めない。
pydantic 2.x 系との依存競合を避けるため、標準の依存性脆弱性監査は `pip-audit` に一本化する。

SBOM は現時点の標準成果物には含めない。
必要になった段階で、`uv export --format cyclonedx1.5` の preview 扱いを確認したうえで別途導入を判断する。

`pip-audit` や `bandit` が非ゼロ終了した場合でも、コマンド自体の失敗とは限らない。
脆弱性や security issue の検出結果として扱い、修正は別 follow-up として切り出す。

## 依存性脆弱性スキャン

### 1. 基本的なセキュリティチェック

```bash
# セキュリティツールのインストール
uv sync --locked --group security

# pip-audit - PyPA / OSV データベース監査
uv run --locked pip-audit

# Bandit - Pythonコードの静的セキュリティ解析
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src -f json -o security-report.json
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
```

### Safety の扱い

`safety` は標準手順では実行しない。

理由:

- 現行の `security` dependency group に含めていない
- pydantic 2.x 系との依存競合がある
- 標準の依存性脆弱性監査は `pip-audit` で代替する

`safety` を再採用する場合は、依存競合、ライセンス、CI 実行条件を再評価してから、別 dependency group または専用 workflow として追加する。

### 2. 継続的セキュリティ監視

```bash
# 日次セキュリティチェック
#!/bin/bash
echo "=== Daily Security Audit ==="
echo "Date: $(date)"
echo ""

echo "1. Dependency Vulnerability Scan (pip-audit):"
uv run --locked pip-audit --format=json --output=audit-report-$(date +%Y%m%d).json
uv run --locked pip-audit

echo ""
echo "2. Static Code Security Analysis (Bandit):"
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src -f json -o bandit-report-$(date +%Y%m%d).json
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level low

echo ""
echo "3. Dependency Tree:"
uv tree

echo "=== Security Audit Complete ==="
```

### 3. 緊急セキュリティアップデート

```bash
# 緊急CVE対応プロセス
echo "=== Emergency Security Update Process ==="

# 1. 現在のバージョン確認
uv tree | grep -E "(fastapi|uvicorn|sqlalchemy|pydantic)"

# 2. 脆弱性影響確認
uv run --locked pip-audit --format=json --output=emergency-audit.json
cat emergency-audit.json | jq '.dependencies[] | select(.vulns | length > 0)'

# 3. 特定パッケージの緊急更新
uv add "fastapi>=0.115.13,<0.116.0"  # 例: セキュリティ修正版
uv add "pydantic>=2.11.7,<2.12.0"     # 例: セキュリティ修正版

# 4. 依存性整合性確認
uv lock --check
uv lock
uv sync --locked --group dev --group test --group security

# 5. セキュリティ再検証
uv run --locked pip-audit

# 6. テスト実行
uv run --locked pytest tests/

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
uv run --locked pip-audit --format=json --output=pre-deploy-audit.json
if ! uv run --locked pip-audit; then
    echo "❌ Vulnerability found! Deployment blocked."
    exit 1
fi

# 2. コードセキュリティ解析
echo "2. Static Security Analysis..."
uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src -f json -o pre-deploy-bandit.json
if ! uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium; then
    echo "⚠️  Security issues found. Review required."
    # 注意: 中レベル以上のセキュリティ問題がある場合は要レビュー
fi

# 3. 設定ファイル検証
echo "3. Configuration Security Check..."
if grep -r "password\|secret\|key" . --exclude-dir=.git --exclude-dir=.venv --exclude="*.md"; then
    echo "⚠️  Potential secrets in code. Manual review required."
fi

# 4. Dockerセキュリティ
echo "4. Container Security Baseline..."
docker run --rm -v "$(pwd)":/app hadolint/hadolint hadolint /app/Dockerfile

echo "✅ Security verification complete!"
echo "📄 Reports generated:"
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
uv tree --outdated > monthly-outdated-$(date +%Y%m).txt
uv tree > monthly-deps-tree-$(date +%Y%m).txt

# 2. 累積脆弱性レポート
echo "2. Cumulative Vulnerability Report:"
uv run --locked pip-audit --format=json --output=monthly-audit-$(date +%Y%m).json

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
        python-version: '3.13.13'
    
    - name: Install uv
      uses: astral-sh/setup-uv@v6
      with:
        version: "0.11.7"
    
    - name: Install dependencies
      run: |
        uv sync --locked --group security
    
    - name: Run pip-audit
      run: |
        uv run --locked pip-audit --format=json --output audit-report.json
        uv run --locked pip-audit
    
    - name: Run Bandit
      run: |
        uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src -f json -o bandit-report.json
        uv run --locked bandit -r app components/libkoiki/src components/koiki_ref_app/src --severity-level medium
    
    - name: Upload Security Reports
      uses: actions/upload-artifact@v4
      with:
        name: security-reports
        path: |
          audit-report.json
          bandit-report.json
```

### GitHub Dependabot

Dependabot は `uv` ecosystem を対象に設定する。
`uv.lock` の更新と security update を GitHub 側の supply chain 導線として併用する。

```yaml
# .github/dependabot.yml
version: 2

updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
```

### GitHub Dependency Review

Pull Request で dependency 変更を検出するため、Dependency Review Action の導入を推奨する。

```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review

on:
  pull_request:
    branches: [ master, develop ]

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
```
