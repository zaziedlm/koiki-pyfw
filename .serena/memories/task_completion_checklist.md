# KOIKI-FW タスク完了チェックリスト

## 開発タスク完了時の必須手順

### 1. テスト実行
```bash
# 全テスト実行
poetry run pytest

# カバレッジ確認
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/

# 特定テスト（必要に応じて）
poetry run pytest tests/unit/app/
poetry run pytest tests/integration/app/api/test_todos_api.py
```

### 2. セキュリティ監査
```bash
# 脆弱性スキャン実行
poetry install --with security
poetry run pip-audit

# 静的セキュリティ解析
poetry run bandit -r . --severity-level medium
```

### 3. 依存関係チェック
```bash
# ロックファイル検証
poetry check --lock

# 依存関係同期確認
poetry show --tree
```

### 4. 型チェック・品質検証
プロジェクトには明示的なlint/typecheckコマンドが見当たらないため、以下を確認：
- Pydantic型ヒントの正しい使用
- async/await パターンの適切な実装
- ImportError等の基本エラーがないこと

### 5. データベース関連（該当する場合）
```bash
# マイグレーション状態確認
alembic current

# 新しいマイグレーション作成（モデル変更時）
alembic revision --autogenerate -m "description"

# マイグレーション実行確認
alembic upgrade head
```

### 6. 統合テスト（重要な変更の場合）
```bash
# セキュリティAPIテスト
./run_security_test.sh test

# アプリケーション起動確認
docker-compose up --build -d
# http://localhost:8000/docs でSwagger UIアクセス確認
```

### 7. ログ・エラー確認
```bash
# アプリケーションログ確認
docker-compose logs -f app

# エラーログの有無確認
# 構造化ログ出力の適切性確認
```

## 重要な注意事項
- **コミット前**: 必ずテストとセキュリティ監査を実行
- **マイグレーション**: モデル変更時は必ずalembicマイグレーション作成
- **セキュリティ**: 認証関連の変更時はセキュリティAPIテストを必須実行
- **依存関係**: Poetry 2.xの依存関係グループを適切に使用