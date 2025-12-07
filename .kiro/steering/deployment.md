# デプロイメントガイド

## Docker構成

### サービス一覧
| サービス | イメージ | ポート | 説明 |
|---------|---------|--------|------|
| db | postgres:15 | 5432 | PostgreSQL |
| app | Dockerfile | 8000 | FastAPI バックエンド |
| frontend | frontend/Dockerfile | 3000 | Next.js フロントエンド |
| keycloak | keycloak:26.3.5 | 8090 | SSO/SAML IdP |

### 起動コマンド
```bash
# 開発環境
docker-compose up --build -d

# ログ確認
docker-compose logs -f app

# 停止
docker-compose down
```

## 環境変数

### バックエンド (.env)
```bash
# データベース
DATABASE_URL=postgresql+asyncpg://koiki_user:koiki_password@db:5432/koiki_todo_db
POSTGRES_USER=koiki_user
POSTGRES_PASSWORD=koiki_password
POSTGRES_DB=koiki_todo_db

# セキュリティ
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# アプリケーション
APP_ENV=development
DEBUG=true
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Redis（オプション）
REDIS_ENABLED=false
REDIS_URL=redis://redis:6379

# SSO設定
SSO_CLIENT_ID=koiki-app
SSO_AUTHORIZATION_ENDPOINT=http://localhost:8090/realms/koiki/protocol/openid-connect/auth
SSO_TOKEN_ENDPOINT=http://localhost:8090/realms/koiki/protocol/openid-connect/token
SSO_JWKS_URI=http://keycloak:8080/realms/koiki/protocol/openid-connect/certs
```

### フロントエンド (frontend/.env.docker)
```bash
NEXT_PUBLIC_API_URL=http://app:8000
NEXT_PUBLIC_API_BASE_URL=http://app:8000/api/v1
NEXT_PUBLIC_API_PREFIX=/api/v1
NODE_ENV=production
```

## データベースマイグレーション

### 自動実行（docker-entrypoint.sh）
- コンテナ起動時に自動でマイグレーション実行
- DB接続確認（最大30回リトライ）

### 手動実行
```bash
# マイグレーション作成
poetry run alembic revision --autogenerate -m "説明"

# 適用
poetry run alembic upgrade head

# ロールバック
poetry run alembic downgrade -1
```

## ヘルスチェック

```bash
# バックエンド
curl http://localhost:8000/health

# フロントエンド
curl http://localhost:3000/api/health

# Keycloak
curl http://localhost:9000/health/ready
```

## Dockerfile特徴

### バックエンド
- Poetry 2.x 最適化（並列インストール）
- 非rootユーザー（appuser）
- カスタム証明書対応
- ヘルスチェック設定

### フロントエンド
- マルチステージビルド（builder → runner）
- 非rootユーザー（nextjs）
- 本番依存関係のみインストール

## CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
- Poetry依存関係インストール
- セキュリティ監査（pip-audit, bandit）
- テスト実行（pytest）
- カバレッジレポート生成
```

## トラブルシューティング

### DB接続エラー
```bash
docker-compose exec db psql -U koiki_user -d koiki_todo_db
docker-compose logs db
```

### マイグレーションエラー
```bash
docker-compose exec app alembic current
docker-compose exec app alembic history
```

### フロントエンド接続エラー
- `NEXT_PUBLIC_API_URL` がコンテナ間通信用（`http://app:8000`）になっているか確認
- CORS設定を確認
