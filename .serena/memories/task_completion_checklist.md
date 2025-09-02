# タスク完了時のチェックリスト

## コード変更後の必須実行項目

### 1. バックエンド（Python）テスト

#### 基本テスト実行
```powershell
# 全テスト実行
poetry run pytest

# カバレッジ付きテスト
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/

# 特定モジュールのテスト
poetry run pytest tests/unit/libkoiki/services/test_変更したサービス.py
```

#### セキュリティテスト（認証・権限変更時）
```bash
# セキュリティAPIテスト実行
./run_security_test.sh test

# セキュリティ設定変更時（初回セットアップ含む）
./run_security_test.sh setup
```

### 2. フロントエンド（TypeScript）テスト

```powershell
cd frontend

# リンティングチェック
npm run lint

# ビルドテスト
npm run build

# テスト実行（設定されている場合）
npm test
```

### 3. データベース変更時

#### マイグレーション（モデル変更時）
```powershell
# 新しいマイグレーション作成
alembic revision --autogenerate -m "変更内容の具体的な説明"

# マイグレーション適用
alembic upgrade head

# マイグレーション履歴確認
alembic history

# 本番適用前の確認
alembic upgrade head --sql  # SQL出力のみ
```

#### データベース整合性確認
```powershell
# テストデータベースでのマイグレーション確認
docker-compose up -d db
docker-compose exec db psql -U koiki_user -d koiki_todo_db -c "\dt"  # テーブル一覧
```

### 4. セキュリティ監査

#### 脆弱性チェック
```powershell
# Python依存関係の脆弱性スキャン
poetry run pip-audit

# コードのセキュリティ静的解析
poetry run bandit -r libkoiki/ app/

# セキュリティ関連依存関係更新確認
poetry install --with security
```

#### フロントエンドセキュリティ
```powershell
cd frontend

# npm auditでの脆弱性チェック
npm audit

# 脆弱性修正（自動修正可能な場合）
npm audit fix
```

### 5. 統合テスト・動作確認

#### ローカル環境での動作確認
```powershell
# バックエンド起動確認
.\start-local-dev.ps1
# または手動起動
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# フロントエンド起動確認
cd frontend
npm run dev
```

#### APIエンドポイント確認
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
- http://localhost:8000/ (ルートエンドポイント)
- http://localhost:3000 (フロントエンド)

#### ログ確認
```powershell
# 構造化ログの適切な出力確認
docker-compose logs -f app

# エラーログの確認
docker-compose logs app | findstr -i error
```

## CI/CD自動実行確認

### GitHub Actions自動実行
以下のブランチへのプッシュ時に自動実行：
- `master`, `develop`
- `dev/*`, `feature/*`, `bugfix/*`

### CI実行内容の確認
1. **環境セットアップ**: Python 3.11.7, Poetry 2.x
2. **依存関係インストール**: Python + Node.js dependencies
3. **テスト実行**: pytest + coverage
4. **リンティング**: ESLint (フロントエンド)
5. **ビルドテスト**: Next.js build

## 本番リリース前の最終チェック

### 1. 全統合テスト実行
```bash
# セキュリティテスト含む全テスト
./run_security_test.sh setup
./run_security_test.sh test
```

### 2. パフォーマンステスト
```powershell
# 本番類似環境でのテスト
docker-compose -f docker-compose.prod.yml up -d  # (存在する場合)

# ロードテスト（必要に応じて）
# ab -n 1000 -c 10 http://localhost:8000/
```

### 3. 環境設定確認
```powershell
# 環境変数の本番設定確認
Get-Content .env.example
# 本番用.envファイルの設定確認

# データベース接続確認
alembic current
alembic history
```

### 4. セキュリティ最終チェック
```powershell
# 包括的セキュリティ監査
poetry install --with security
poetry run pip-audit
poetry run bandit -r libkoiki/ app/

cd frontend
npm audit
```

## 推奨開発ワークフロー

1. **ブランチ作成** (`git checkout -b feature/新機能名`)
2. **コード変更**
3. **ローカルテスト** (`poetry run pytest`, `npm run lint`)
4. **動作確認** (`.\start-local-dev.ps1`, `npm run dev`)
5. **セキュリティチェック** (必要に応じて)
6. **Git操作**
   ```powershell
   git add .
   git commit -m "feat: 新機能の説明"
   git push origin feature/新機能名
   ```
7. **プルリクエスト作成** (GitHub UI)
8. **CI自動実行確認** (GitHub Actions)
9. **コードレビュー後マージ**

## トラブルシューティング

### よくある問題と対処法
```powershell
# Poetry環境の再構築
poetry env remove python
poetry install

# Node.js依存関係の再インストール
cd frontend
Remove-Item node_modules -Recurse -Force
Remove-Item package-lock.json -Force
npm install

# Docker環境のクリーンアップ
docker-compose down -v
docker-compose up --build -d
```