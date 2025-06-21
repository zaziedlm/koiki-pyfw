# KOIKI-FW コンテナ配備コマンド一覧

このドキュメントでは、KOIKIフレームワークのDockerコンテナによる各種配備シナリオと必要なコマンドを説明します。[`docker-entrypoint.sh`](docker-entrypoint.sh)の自動実行機能を考慮した最適な手順を示しています。

**更新**: Poetry 2.x移行とセキュリティ修正完了（2025-06-21）

## 1. 初回環境構築時

```bash
# 環境変数ファイルの準備
cp .env.example .env
# 必要に応じて.envファイルを編集

# コンテナのビルドと起動
docker-compose up --build -d
# この過程で以下が自動的に実行されます:
# - データベース接続の確認（最大30回リトライ）
# - alembic/versionsディレクトリの確認と作成
# - 初期マイグレーション実行（または必要に応じて自動生成）

# アプリケーション起動ログの確認
docker-compose logs -f app
```

## 2. 日常の開発作業

```bash
# コンテナ起動（既にビルド済みの場合）
docker-compose up -d
# entrypoint.shによりマイグレーションが自動実行されます

# コンテナ停止
docker-compose down

# ログ確認
docker-compose logs -f app
```

## 3. アプリケーションコード修正後

```bash
# ソースコードの変更のみの場合
# （多くのコードはボリュームマウントされているため変更が即時反映）
# 特別な操作は必要ありません

# 依存関係やDockerfile変更時は再ビルドが必要
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 4. データモデル変更時（マイグレーション作成）

```bash
# 1. モデルコードを変更

# 2. 新しいマイグレーションの作成
docker-compose exec app alembic revision --autogenerate -m "変更内容を説明"

# 3. コンテナ再起動でマイグレーションが自動適用
docker-compose restart app

# 4. マイグレーション適用確認
docker-compose logs -f app
```

## 5. マイグレーション関連操作

```bash
# 現在のマイグレーション状態確認
docker-compose exec app alembic current

# マイグレーション履歴の確認
docker-compose exec app alembic history

# 特定バージョンへのロールバック（必要時のみ）
docker-compose exec app alembic downgrade <revision_id>
```

## 6. 環境のクリーンアップ

```bash
# コンテナと関連リソースの停止・削除（データは保持）
docker-compose down

# データも含めた完全クリーンアップ
docker-compose down -v

# 全ての環境を初期状態から再構築
docker-compose up --build -d
```

## 7. トラブルシューティング

```bash
# コンテナの状態確認
docker-compose ps

# entrypoint.shを含む詳細ログの確認
docker-compose logs -f app

# データベース接続確認
docker-compose exec db psql -U koiki_user -d koiki_todo_db

# コンテナ内シェルアクセス
docker-compose exec app bash

# 強制的な再ビルド
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

## 8. 本番環境デプロイ準備

```bash
# 本番用.envファイルの準備
cp .env.example .env.production
# 本番環境用の設定に編集

# 本番環境用イメージのビルド
docker-compose -f docker-compose.production.yml build

# イメージのプッシュ（レジストリがある場合）
docker-compose -f docker-compose.production.yml push
```

## 9. セキュリティ監査とテスト (2025-06-21 追加)

```bash
# セキュリティ監査の実行
docker-compose exec app pip-audit

# 静的セキュリティ解析
docker-compose exec app bandit -r app/ libkoiki/

# 包括的APIテスト（開発環境）
curl -s http://localhost:8000/ | jq .
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/api/v1/health | jq .

# ユーザー登録テスト
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}' | jq .

# 認証トークン取得テスト
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}' | jq .
```

## アプリケーションへのアクセス

コンテナ起動後、以下のURLでアプリケーションにアクセスできます：

* API ドキュメント (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
* API ドキュメント (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)
* ルートエンドポイント: [http://localhost:8000/](http://localhost:8000/)

## 技術的な説明

### docker-entrypoint.shの機能

コンテナ起動時には[`docker-entrypoint.sh`](docker-entrypoint.sh)スクリプトが実行され、以下の処理が自動的に行われます：

1. **データベース接続確認**：
   - DATABASE_URL環境変数から接続情報を解析
   - 最大30回のリトライでデータベースへの接続を確認

2. **マイグレーション準備**：
   - `alembic/versions`ディレクトリの存在確認と作成

3. **マイグレーション実行**：
   - `alembic upgrade head`でマイグレーションを実行
   - マイグレーションファイルが存在しない場合は初期マイグレーションを自動生成

この自動化により、開発者はデータベースセットアップの多くの手順を意識する必要がなくなり、アプリケーション開発に集中できます。

## 最新のPoetry 2.x対応状況

### 依存性管理の改善点
- **Poetry 2.1.0**: 最新のPoetry 2.xシステムを採用
- **PEP 621準拠**: `pyproject.toml`が標準的な設定構造に移行
- **セキュリティ強化**: 全脆弱性（PYSEC-2024-38, PYSEC-2024-232/233, GHSA-f96h-pmfr-66vw）を修正
- **Python 3.13対応**: 完全な互換性を確保

### 主要な更新内容
```toml
# 主要パッケージのバージョン更新例
fastapi = ">=0.115.13,<0.116.0"     # セキュリティ修正版
pydantic = ">=2.11.7,<2.12.0"       # 検証機能強化版
uvicorn = ">=0.34.3,<0.35.0"        # パフォーマンス大幅改善
pytest = ">=8.4.1,<8.5.0"          # テストフレームワーク最新版
```

詳細な更新履歴と企業向け実装戦略については、[ENTERPRISE_DEPENDENCY_STRATEGY.md](ENTERPRISE_DEPENDENCY_STRATEGY.md)を参照してください。
