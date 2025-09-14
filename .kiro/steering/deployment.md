# デプロイメントガイド

## デプロイメント戦略

KOIKI-FWは、Docker化されたマイクロサービスアーキテクチャを採用し、スケーラブルで信頼性の高いデプロイメントを実現します。

## 環境構成

### 開発環境 (Development)
- **目的**: ローカル開発・デバッグ
- **構成**: Docker Compose
- **データベース**: PostgreSQL (Docker)
- **Redis**: Docker コンテナ
- **フロントエンド**: Next.js開発サーバー

```bash
# 開発環境起動
docker-compose up --build -d

# ログ確認
docker-compose logs -f app
```

### ステージング環境 (Staging)
- **目的**: 本番前テスト・統合テスト
- **構成**: 本番環境と同等
- **データベース**: PostgreSQL (専用インスタンス)
- **Redis**: 専用インスタンス
- **監視**: 基本的なメトリクス収集

### 本番環境 (Production)
- **目的**: 本番サービス提供
- **構成**: 高可用性・スケーラブル
- **データベース**: PostgreSQL (レプリケーション構成)
- **Redis**: クラスター構成
- **監視**: 包括的な監視・アラート

## Docker構成

### バックエンド Dockerfile
```dockerfile
FROM python:3.11-slim

# カスタム証明書とCA証明書の設定
COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# SSL証明書環境変数
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Poetry 2.x 最適化設定
ENV POETRY_VERSION=2.1.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_VENV_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/opt/poetry-cache \
    POETRY_INSTALLER_PARALLEL=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    PATH="$POETRY_HOME/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Poetry インストール
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION \
    && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# セキュリティ強化: 非rootユーザー作成
RUN adduser --disabled-password --gecos "" appuser

# アプリケーションコードコピー
COPY ./app ./app
COPY ./libkoiki ./libkoiki
COPY ./alembic ./alembic
COPY ./alembic.ini ./
COPY ./main.py ./
COPY ./ops ./ops

# Poetry依存関係ファイル
COPY pyproject.toml poetry.lock README.md ./

# 依存関係インストール
RUN mkdir -p $POETRY_CACHE_DIR \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    && poetry cache clear --all pypi

# エントリポイントスクリプト
COPY docker-entrypoint.sh ./
RUN chmod +x /app/docker-entrypoint.sh

# ディレクトリ作成と権限設定
RUN mkdir -p /app/alembic/versions && chown -R appuser:appuser /app

# 非rootユーザーに切り替え
USER appuser

# エントリポイント設定
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### フロントエンド Dockerfile
```dockerfile
# マルチステージビルド: Builder stage
FROM node:22-slim AS builder

# カスタム証明書設定
COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget curl && \
    update-ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Node.js環境変数
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# 依存関係インストール
COPY package*.json ./
RUN npm ci

# ソースコピーとビルド
RUN mkdir -p /app/public
COPY . .
RUN npm run build

# Runtime stage
FROM node:22-slim AS runner

# カスタム証明書設定
COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget curl && \
    update-ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 環境変数
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

# 非rootユーザー作成
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs nextjs

# 本番依存関係インストール
COPY --chown=nextjs:nodejs package*.json ./
RUN npm ci --omit=dev

# ビルド成果物コピー
COPY --chown=nextjs:nodejs --from=builder /app/.next /app/.next
COPY --chown=nextjs:nodejs --from=builder /app/public /app/public

# 非rootユーザーに切り替え
USER nextjs

EXPOSE 3000

# ヘルスチェック（Node.js内蔵httpモジュール使用）
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))" || exit 1

CMD ["npm", "start"]
```

## Docker Compose構成

### 開発用 docker-compose.yml
```yaml
services:
  db:
    image: postgres:15
    container_name: osskk_postgres_db
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-koiki_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-koiki_password}
      POSTGRES_DB: ${POSTGRES_DB:-koiki_todo_db}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: always
    # PostgreSQLパフォーマンス設定
    command:
      - "postgres"
      - "-c"
      - "max_connections=100"
      - "-c"
      - "shared_buffers=256MB"

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: osskk_fastapi_app
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: osskk_nextjs_frontend
    depends_on:
      - app
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env.docker
    environment:
      # コンテナ間通信用API URL
      - NEXT_PUBLIC_API_BASE_URL=http://app:8000/api/v1
      - NEXT_PUBLIC_API_PREFIX=/api/v1
      - NEXT_PUBLIC_API_URL=http://app:8000
      - NODE_ENV=production
    restart: always
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  postgres_data:
```

## CI/CDパイプライン

### GitHub Actions ワークフロー
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11.7'
    
    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run tests
      run: |
        poetry run pytest --cov=app --cov=libkoiki
        poetry run bandit -r app/ libkoiki/
        poetry run pip-audit
    
    - name: Build Docker image
      run: docker build -t koiki-fw:${{ github.sha }} .

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
    - name: Deploy to Staging
      run: |
        # ステージング環境へのデプロイ処理
        echo "Deploying to staging..."

  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Production
      run: |
        # 本番環境へのデプロイ処理
        echo "Deploying to production..."
```

## データベースマイグレーション

### データベースマイグレーション

#### 自動マイグレーション（docker-entrypoint.sh）
```bash
#!/bin/bash
set -e

# データベース接続チェック（最大30回リトライ）
echo "データベースへの接続を確認中..."
retry 30 python -c "
import psycopg2
import os
from urllib.parse import urlparse

# DATABASE_URLを解析して接続テスト
db_url = os.environ.get('DATABASE_URL', '')
if '+asyncpg' in db_url:
    db_url = db_url.replace('+asyncpg', '')
parts = urlparse(db_url)
psycopg2.connect(
    dbname=parts.path[1:],
    user=parts.username,
    password=parts.password,
    host=parts.hostname,
    port=parts.port or 5432
)
"

# alembic/versionsディレクトリ確認・作成
if [ ! -d "/app/alembic/versions" ]; then
    mkdir -p /app/alembic/versions
    chown -R appuser:appuser /app/alembic/versions
fi

# マイグレーション実行
echo "データベースマイグレーションを実行中..."
alembic upgrade head || {
    # 初期マイグレーションが存在しない場合の処理
    if [ -z "$(ls -A /app/alembic/versions)" ]; then
        alembic revision --autogenerate -m "initial_migration"
        alembic upgrade head
    fi
}

exec "$@"
```

#### 手動マイグレーション
```bash
# マイグレーション実行前のバックアップ
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# マイグレーション実行
poetry run alembic upgrade head

# 確認
poetry run alembic current
```

### ロールバック手順
```bash
# 現在のリビジョン確認
poetry run alembic current

# 1つ前のリビジョンにロールバック
poetry run alembic downgrade -1

# 特定のリビジョンにロールバック
poetry run alembic downgrade <revision_id>
```

## 監視・ログ

### Prometheus メトリクス
```python
# app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Prometheusメトリクス設定
Instrumentator().instrument(app).expose(app)
```

### ログ集約
```yaml
# docker-compose.yml (本番用)
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### ヘルスチェック

#### バックエンドヘルスチェック
```python
# app/main.py
@app.get("/health", tags=["Health Check"])
async def health_check(request: Request):
    """システムヘルスチェック"""
    from datetime import datetime
    
    logger.debug("Health check endpoint called.")
    return {
        "status": "healthy",
        "service": "koiki-framework",
        "version": "0.6.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/", tags=["Service Info"])
async def root(request: Request):
    """API情報とドキュメントリンク"""
    return {
        "service": "KOIKI Framework API",
        "version": "0.6.0",
        "docs": "/docs",
        "health": "/health",
    }
```

#### フロントエンドヘルスチェック
```typescript
// frontend/src/app/api/health/route.ts
export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'koiki-frontend',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
}
```

#### Dockerヘルスチェック
```dockerfile
# バックエンド
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# フロントエンド
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))" || exit 1
```

## セキュリティ設定

### セキュリティ設定

#### 環境変数設定
```bash
# .env ファイル例
SECRET_KEY="your-super-secret-key-here"
DATABASE_URL="postgresql+asyncpg://user:password@db:5432/dbname"
REDIS_URL="redis://redis:6379"
APP_ENV="production"
CORS_ORIGINS="https://yourdomain.com"

# JWT設定
JWT_SECRET="your-jwt-secret-key"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# セキュリティ設定
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STRATEGY="redis"
RATE_LIMIT_DEFAULT="100/minute"
```

#### カスタム証明書対応
```dockerfile
# Dockerfileでのカスタム証明書設定
COPY docker/certs/nscacert.pem /usr/local/share/ca-certificates/nscacert.crt
RUN update-ca-certificates

# 環境変数での証明書パス指定
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/nscacert.crt
```

### SSL/TLS設定（フルスタック対応）
```nginx
# nginx.conf
upstream backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

upstream frontend {
    server frontend1:3000;
    server frontend2:3000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # フロントエンド（Next.js）
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket対応（必要に応じて）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # バックエンドAPI（FastAPI）
    location /api/v1/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS対応
        add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-CSRF-Token" always;
        add_header Access-Control-Allow-Credentials true always;
    }
    
    # 静的ファイル（Next.js）
    location /_next/static/ {
        proxy_pass http://frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## スケーリング

### 水平スケーリング
```yaml
# docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### ロードバランサー設定
```nginx
upstream backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

upstream frontend {
    server frontend1:3000;
    server frontend2:3000;
}
```

## バックアップ・復旧

### データベースバックアップ
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQLバックアップ
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 古いバックアップ削除（30日以上）
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

### 災害復旧手順
1. **システム停止**: サービス停止・メンテナンスモード
2. **データ復旧**: バックアップからデータベース復元
3. **設定確認**: 環境変数・設定ファイル確認
4. **サービス再開**: 段階的なサービス復旧
5. **動作確認**: 全機能の動作テスト

## トラブルシューティング

### よくある問題と解決方法

**データベース接続エラー**
```bash
# 接続確認
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# ログ確認
docker-compose logs db
```

**メモリ不足**
```bash
# メモリ使用量確認
docker stats

# コンテナリソース制限
docker-compose up --scale app=2
```

**パフォーマンス問題**
```bash
# スロークエリログ確認
docker-compose exec db tail -f /var/log/postgresql/postgresql.log

# APMツール活用
# New Relic, DataDog等の導入検討
```