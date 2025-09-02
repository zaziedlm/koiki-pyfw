# 開発コマンド（Windows環境）

## 環境セットアップ

### Docker環境セットアップ（推奨）
```powershell
# 環境変数ファイルの準備
Copy-Item .env.example .env
# .envファイルを編集してデータベース接続情報等を設定

# コンテナのビルドと起動
docker-compose up --build -d

# アプリケーションログの確認
docker-compose logs -f app
```

### ローカル開発環境（PowerShell）
```powershell
# KOIKI専用開発スクリプト（推奨）
.\start-local-dev.ps1

# 手動セットアップの場合
$env:DATABASE_URL = "postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db"
$env:APP_ENV = "development"
$env:DEBUG = "True"
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## テスト実行

### セキュリティAPIテスト（推奨）
```bash
# プロジェクトルートから一発実行
./run_security_test.sh test

# 初回実行（セットアップ含む）
./run_security_test.sh setup

# ヘルプ表示
./run_security_test.sh help
```

### Python単体・統合テスト
```powershell
# 全テスト実行
poetry run pytest

# カバレッジレポート付きテスト
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/

# 特定のテスト実行
poetry run pytest tests/unit/libkoiki/services/test_user_service.py

# 詳細ログ出力
poetry run pytest -v -s

# 統合テストのみ実行
poetry run pytest tests/integration/

# 単体テストのみ実行
poetry run pytest tests/unit/
```

## フロントエンド開発

### フロントエンド開発サーバー
```powershell
# frontendディレクトリに移動
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev

# ビルド（本番用）
npm run build

# ビルド後のプレビュー
npm run start
```

## データベース管理（Alembic）

### マイグレーション操作
```powershell
# 最新マイグレーション適用
alembic upgrade head

# 新しいマイグレーション作成
alembic revision --autogenerate -m "変更の説明"

# マイグレーション履歴確認
alembic history

# 特定のバージョンにロールバック
alembic downgrade <revision_id>

# 現在のマイグレーション状態確認
alembic current
```

## 開発サーバー起動

### バックエンドサーバー
```powershell
# 開発モード（自動リロード）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# プロダクションモード
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 複数ワーカー
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## セキュリティ監査

### セキュリティチェック
```powershell
# 脆弱性スキャン
poetry run pip-audit

# セキュリティ静的解析
poetry run bandit -r libkoiki/ app/

# セキュリティ関連依存関係インストール
poetry install --with security
```

## コードフォーマット・リンティング

### Python
```powershell
# Poetryグループで管理（pyproject.tomlで設定）
poetry install --with dev

# 型チェック（mypyなど、設定されている場合）
# フォーマット（blackなど、設定されている場合）
```

### TypeScript/JavaScript
```powershell
cd frontend

# ESLintによるリンティング
npm run lint

# フォーマット（設定されている場合）
npm run format
```

## ログ・モニタリング

### ログ確認
```powershell
# アプリケーションログ
docker-compose logs -f app

# データベースログ
docker-compose logs -f db

# 全サービスログ
docker-compose logs -f

# ログファイル確認（構造化ログ）
Get-Content -Path logs/app.log -Tail 50 -Wait
```

## Windowsシステムユーティリティ

### 基本コマンド
```powershell
# ディレクトリ一覧
Get-ChildItem
ls  # PowerShell alias

# ファイル検索
Get-ChildItem -Recurse -Name "*.py"
Get-ChildItem -Recurse -Name "*.ts" -Path frontend/

# プロセス確認
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# ポート使用状況
netstat -an | findstr :8000
netstat -an | findstr :3000  # フロントエンド

# 環境変数確認
Get-ChildItem Env: | Where-Object {$_.Name -like "*DATABASE*"}
```

### Git操作
```powershell
# 状態確認
git status

# ブランチ確認
git branch -a

# 変更をステージング・コミット
git add .
git commit -m "feat: 機能追加の説明"

# プッシュ（CI自動実行される）
git push origin dev/frontend-app_20250729
```