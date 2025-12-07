# 技術スタック

## バックエンド

### コアフレームワーク
- **Python**: >=3.11.7（Python 3.13対応）
- **FastAPI**: >=0.115.13（ASGI Webフレームワーク）
- **Uvicorn**: >=0.34.3（ASGIサーバー）
- **Poetry 2.x**: 依存関係管理（PEP 621準拠）

### データベース
- **PostgreSQL 15**: メインデータベース
- **SQLAlchemy 2.0**: 非同期ORM（asyncpg >=0.30.0）
- **Alembic**: >=1.16.2（マイグレーション管理）

### 認証・セキュリティ
- **python-jose**: >=3.4.0（JWT処理）
- **passlib[bcrypt]**: パスワードハッシュ化
- **slowapi**: >=0.1.8（レート制限）
- **python3-saml**: SAML 2.0認証
- **jwcrypto**: JWKS対応

### その他
- **Pydantic**: >=2.11.7（データ検証）
- **structlog**: >=25.4.0（構造化ログ）
- **Redis**: >=6.2.0（キャッシュ、イベント）
- **httpx**: >=0.28.1（HTTPクライアント）

## フロントエンド

### コアフレームワーク
- **Next.js**: 15.5.2（App Router）
- **React**: 19.1.0
- **TypeScript**: ^5

### UI・スタイリング
- **Tailwind CSS**: ^4
- **Radix UI**: アクセシブルコンポーネント
- **Lucide React**: アイコン

### 状態管理・データ取得
- **TanStack Query**: ^5.83.0（サーバー状態）
- **Zustand**: ^5.0.6（クライアント状態）
- **React Hook Form**: ^7.61.1 + **Zod**: ^4.0.10（フォーム）

## インフラ

- **Docker / Docker Compose**: コンテナ化
- **Keycloak**: 26.3.5（SSO/SAML IdP）
- **GitHub Actions**: CI/CD

---

## よく使うコマンド

### 開発環境起動
```bash
# Docker（推奨）
docker-compose up --build -d

# ローカル（バックエンド）
poetry install
poetry run uvicorn app.main:app --reload --port 8000

# ローカル（フロントエンド）
cd frontend && npm install && npm run dev
```

### テスト
```bash
# セキュリティAPIテスト
./run_security_test.sh test

# ユニットテスト
poetry run pytest

# カバレッジ付き
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/
```

### データベース
```bash
# マイグレーション作成
poetry run alembic revision --autogenerate -m "説明"

# マイグレーション適用
poetry run alembic upgrade head

# 現在のリビジョン確認
poetry run alembic current
```

### セキュリティ監査
```bash
poetry install --with security
poetry run pip-audit
poetry run bandit -r app/ libkoiki/
```

### フロントエンド
```bash
cd frontend
npm run dev          # 開発サーバー
npm run build        # ビルド
npm run lint         # ESLint
npm run check-types  # TypeScript型チェック
```
