# KOIKI-FW 推奨開発コマンド

## Poetry 2.x 環境セットアップ
```bash
# Poetry 2.x パフォーマンス設定
poetry config installer.parallel true
poetry config installer.max-workers 10
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# 依存関係の検証とインストール
poetry check --lock
poetry install

# 依存関係グループ別インストール
poetry install --with dev          # 開発依存関係込み
poetry install --with test         # テスト依存関係込み
poetry install --with dev,test     # 複数グループ
poetry install --only=main         # 本番依存関係のみ
```

## 開発実行コマンド
```bash
# Docker Compose実行（推奨）
docker-compose up --build -d

# ローカル実行（PostgreSQL要設定）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Poetry環境アクティベート
poetry shell
```

## テスト実行
```bash
# セキュリティAPIテスト（推奨ワンコマンド）
./run_security_test.sh test

# 全テスト実行
poetry run pytest

# 特定テスト実行
poetry run pytest tests/unit/test_hello.py
poetry run pytest tests/integration/app/api/test_todos_api.py

# カバレッジ付きテスト
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing --cov-report=html tests/
```

## データベース管理
```bash
# マイグレーション作成
alembic revision --autogenerate -m "description"

# マイグレーション実行
alembic upgrade head

# マイグレーション状態確認
alembic current
```

## セキュリティ監査
```bash
# 脆弱性スキャン
poetry install --with security
poetry run pip-audit
poetry run pip-audit --format=json --output=security-audit.json

# 静的セキュリティ解析
poetry run bandit -r . --severity-level medium
poetry run bandit -r . -f json -o security-bandit.json
```

## 依存関係管理
```bash
# 依存関係ツリー表示
poetry show --tree
poetry show --tree --only=main     # 本番依存関係のみ

# 更新チェック
poetry show --outdated

# 環境情報
poetry env info
poetry config --list
```