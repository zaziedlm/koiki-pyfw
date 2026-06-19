# よく使うコマンド

## このステアリングファイルについて

このファイルはKiroでの開発作業で頻繁に使用するコマンドをまとめています。

---

## 依存関係管理（uv）

### 基本コマンド

```bash
# 依存関係の同期（lockfileから）
uv sync --locked

# 開発用依存関係を含めて同期
uv sync --locked --all-extras

# セキュリティグループを含めて同期
uv sync --locked --group security
```

**重要**: `uv.lock` が依存関係の正本です。常に `--locked` オプションを使用してください。

---

## アプリケーション起動

### バックエンド（FastAPI）

```bash
# 開発サーバー起動（ホットリロード有効）
uv run --locked uvicorn koiki_ref_app.asgi:app --reload --port 8000

# 本番モード起動
uv run --locked uvicorn koiki_ref_app.asgi:app --host 0.0.0.0 --port 8000
```

**注意**: `app.main:app` は互換性のためのレガシーエントリーポイントです。新規作業では `koiki_ref_app.asgi:app` を使用してください。

### フロントエンド（Next.js）

```bash
cd frontend

# 開発サーバー起動
npm run dev

# 本番ビルド
npm run build

# 本番サーバー起動
npm run start

# リント実行
npm run lint
```

---

## データベース管理（Alembic）

### マイグレーション

```bash
# マイグレーションファイル自動生成
uv run --locked alembic revision --autogenerate -m "説明文"

# マイグレーション適用
uv run --locked alembic upgrade head

# 1つ前にロールバック
uv run --locked alembic downgrade -1

# 現在のマイグレーション状態確認
uv run --locked alembic current

# マイグレーション履歴表示
uv run --locked alembic history
```

**注意**: マイグレーションファイルは `components/koiki_ref_app/alembic/versions/` に生成されます。

---

## テスト実行

### pytest

```bash
# 全テスト実行
uv run --locked pytest

# 特定のテストファイル実行
uv run --locked pytest tests/test_auth.py

# 特定のテスト関数実行
uv run --locked pytest tests/test_auth.py::test_login

# カバレッジ付きで実行
uv run --locked pytest --cov=components/libkoiki --cov=components/koiki_ref_app

# 詳細出力
uv run --locked pytest -v

# 失敗したテストのみ再実行
uv run --locked pytest --lf
```

### テストディレクトリ

- `components/libkoiki/tests/`: フレームワークテスト
- `components/koiki_ref_app/tests/`: アプリケーションテスト
- `tests/`: 統合テスト

---

## セキュリティ監査

```bash
# 脆弱性スキャン
uv run --locked pip-audit

# 静的解析（Bandit）
uv run --locked bandit -r components/libkoiki/src components/koiki_ref_app/src

# セキュリティテスト実行（スクリプト経由）
./run_security_test.sh test
```

---

## Docker操作

### 基本コマンド

```bash
# 全サービス起動（ビルド含む）
docker-compose up --build -d

# ログ確認
docker-compose logs -f app
docker-compose logs -f frontend

# サービス停止
docker-compose down

# サービス再起動
docker-compose restart app

# コンテナ内でコマンド実行
docker-compose exec app uv run --locked pytest
docker-compose exec db psql -U koiki_user -d koiki_todo_db
```

### ヘルスチェック

```bash
# バックエンド
curl http://localhost:8000/health

# フロントエンド
curl http://localhost:3000/api/health

# Keycloak
curl http://localhost:9000/health/ready
```

---

## 開発ワークフロー例

### 新機能開発の典型的な流れ

```bash
# 1. 依存関係を最新化
uv sync --locked

# 2. 開発サーバー起動（別ターミナル）
uv run --locked uvicorn koiki_ref_app.asgi:app --reload --port 8000

# 3. フロントエンド起動（別ターミナル）
cd frontend && npm run dev

# 4. コード変更後、テスト実行
uv run --locked pytest tests/test_new_feature.py

# 5. マイグレーション作成（モデル変更時）
uv run --locked alembic revision --autogenerate -m "Add new_feature table"

# 6. マイグレーション適用
uv run --locked alembic upgrade head

# 7. セキュリティチェック
uv run --locked pip-audit
uv run --locked bandit -r components/libkoiki/src components/koiki_ref_app/src
```

---

## トラブルシューティング

### よくある問題と解決方法

**依存関係の問題:**
```bash
# lockfileを再生成
uv lock

# キャッシュをクリア
uv cache clean
```

**データベース接続エラー:**
```bash
# PostgreSQL接続確認
docker-compose exec db psql -U koiki_user -d koiki_todo_db

# ログ確認
docker-compose logs db
```

**マイグレーションエラー:**
```bash
# 現在の状態確認
uv run --locked alembic current

# 履歴確認
uv run --locked alembic history

# 強制的に最新に
uv run --locked alembic stamp head
```

---

## 環境変数

### 主要な環境変数

**バックエンド (.env):**
```bash
DATABASE_URL=postgresql+asyncpg://koiki_user:koiki_password@localhost:5432/koiki_todo_db
SECRET_KEY=your-secret-key
DEBUG=True
APP_ENV=development
```

**フロントエンド (frontend/.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_PREFIX=/api/v1
```

---

## Skills との協調

コマンド実行時には以下のSkillsが役立ちます：

- **koiki-testing**: テスト作成・実行の詳細ガイダンス
- **koiki-libkoiki-feature-work**: フレームワーク層（components/libkoiki/）での開発
- **koiki-refapp-feature-work**: リファレンスアプリ層（components/koiki_ref_app/）での開発
- **koiki-business-app-feature-work**: ダウンストリーム業務アプリ層（apps/）での開発

---

## 参照先

詳細な情報は以下を参照してください：

- **docs/agent/environment.md**: 環境固有の問題と回避策
- **docs/agent/testing.md**: テスト戦略の詳細
- **AGENTS.md**: エージェント向けエントリーポイント
