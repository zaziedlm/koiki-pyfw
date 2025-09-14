# 技術スタック・ビルドシステム

## バックエンドスタック

### コアフレームワーク
- **FastAPI** (>=0.115.13): API構築のためのモダンで高速なWebフレームワーク
- **Python** (>=3.11.7): 必須Pythonバージョン
- **Uvicorn** (>=0.34.3): 本番デプロイ用ASGIサーバー

### データベース・ORM
- **PostgreSQL**: メインデータベース（Docker: postgres:15）
- **SQLAlchemy** (>=2.0.23): モダンな構文を持つ非同期ORM
- **Alembic** (>=1.16.2): データベースマイグレーション管理
- **asyncpg** (>=0.30.0): 非同期PostgreSQLドライバー

### セキュリティ・認証
- **python-jose** (>=3.4.0): JWTトークン処理
- **passlib[bcrypt]** (>=1.7.4): パスワードハッシュ化
- **slowapi** (>=0.1.8): レート制限

### データ検証・設定
- **Pydantic** (>=2.11.7): データ検証と設定管理
- **pydantic-settings** (>=2.10.0): 設定管理

### キャッシュ・パフォーマンス
- **Redis** (>=6.2.0): キャッシュとセッションストレージ
- **Celery**: 非同期タスク処理（オプション）

### 監視・ログ
- **structlog** (>=25.4.0): 構造化ログ
- **prometheus-fastapi-instrumentator**: メトリクス収集

## フロントエンドスタック

### コアフレームワーク
- **Next.js** (15.5.2): SSR/SSG対応Reactフレームワーク
- **React** (19.1.0): UIライブラリ
- **TypeScript** (^5): 型安全性

### UI・スタイリング
- **Tailwind CSS** (^4): ユーティリティファーストCSSフレームワーク
- **Radix UI**: アクセシブルなコンポーネントプリミティブ
- **Lucide React**: アイコンライブラリ
- **next-themes**: ダーク/ライトモード対応

### 状態管理・データ取得
- **TanStack Query** (^5.83.0): サーバー状態管理
- **Zustand** (^5.0.6): クライアント状態管理
- **React Hook Form** (^7.61.1): フォーム処理
- **Zod** (^4.0.10): スキーマ検証

## ビルドシステム・パッケージ管理

### Python依存関係
- **Poetry**: メイン依存関係管理
- **pip**: 代替パッケージインストール
- **pyproject.toml**: モダンなPythonプロジェクト設定（PEP 621準拠）

### Node.js依存関係
- **npm**: フロントエンド用パッケージ管理
- **package.json**: フロントエンド依存関係設定

## よく使用するコマンド

### 開発環境セットアップ
```bash
# バックエンドセットアップ
poetry install
poetry run alembic upgrade head

# フロントエンドセットアップ
cd frontend
npm install

# Dockerセットアップ（推奨）
docker-compose up --build -d
```

### テスト
```bash
# セキュリティAPIテスト（推奨）
./run_security_test.sh test

# ユニットテスト
poetry run pytest
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/

# フロントエンドテスト
cd frontend
npm run lint
```

### 開発サーバー
```bash
# バックエンド（ローカル）
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# フロントエンド（ローカル）
cd frontend
npm run dev

# フルスタック（Docker）
docker-compose up -d
```

### データベース管理
```bash
# マイグレーション作成
poetry run alembic revision --autogenerate -m "説明"

# マイグレーション適用
poetry run alembic upgrade head

# マイグレーションロールバック
poetry run alembic downgrade -1
```

### セキュリティ・品質
```bash
# セキュリティ監査
poetry run pip-audit
poetry run bandit -r app/ libkoiki/

# コードフォーマット（設定済みの場合）
poetry run black app/ libkoiki/
poetry run isort app/ libkoiki/
```

## 環境設定

### 必要な環境ファイル
- `.env`: メイン環境設定
- `.env.example`: 環境変数テンプレート
- `frontend/.env.local`: フロントエンド固有変数

### 主要環境変数
- `DATABASE_URL`: PostgreSQL接続文字列
- `REDIS_URL`: Redis接続文字列
- `SECRET_KEY`: JWT署名キー
- `APP_ENV`: 環境（development/production）
- `CORS_ORIGINS`: 許可されたCORSオリジン

## 開発ワークフロー

### 新機能開発手順
1. **要件定義**: 機能要件を明確化
2. **設計**: アーキテクチャ設計とAPI設計
3. **実装**: バックエンド → フロントエンド順で実装
4. **テスト**: ユニットテスト → 統合テスト
5. **デプロイ**: ステージング → 本番環境

### コード品質管理
- **型安全性**: TypeScript/Pydantic活用
- **テストカバレッジ**: 80%以上を目標
- **セキュリティ**: 定期的な脆弱性スキャン
- **パフォーマンス**: 非同期処理とキャッシュ活用

### Cookie認証実装
- **CSRF保護**: 全ての状態変更操作で必須
- **セッション管理**: HTTPOnlyクッキーでセキュア
- **トークンリフレッシュ**: 自動更新機能

## フルスタック統合

### API統合
- **Route Handlers**: Next.js App RouterのAPI Routesでバックエンドプロキシ
- **Cookie認証**: HTTPOnlyクッキーによるセキュアな認証
- **CSRF保護**: 自動CSRF トークン生成・検証
- **型共有**: TypeScript型定義とPydanticスキーマの整合性

### 開発環境統合
```bash
# フルスタック開発環境起動
docker-compose up --build -d

# 個別サービス起動
# バックエンド
poetry run uvicorn app.main:app --reload --port 8000

# フロントエンド  
cd frontend && npm run dev

# データベースマイグレーション
poetry run alembic upgrade head
```

### 本番環境統合
```bash
# 本番ビルド
docker-compose -f docker-compose.prod.yml up --build -d

# ヘルスチェック
curl http://localhost:8000/health  # バックエンド
curl http://localhost:3000/api/health  # フロントエンド
```

### 統合テスト
```bash
# フルスタックテスト
./run_security_test.sh test

# E2Eテスト（Playwright等）
cd frontend && npm run test:e2e

# API統合テスト
poetry run pytest tests/integration/
```

### パフォーマンス最適化
- **SSR/SSG**: Next.jsによる最適化されたレンダリング
- **コード分割**: 動的インポートによる最適化
- **キャッシュ戦略**: Redis + TanStack Queryによる多層キャッシュ
- **CDN統合**: 静的アセットの配信最適化