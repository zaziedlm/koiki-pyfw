# KOIKI-FW コンテナ配備コマンド一覧

このドキュメントでは、KOIKIフレームワークのDockerコンテナによる各種配備シナリオと必要なコマンドを説明します。[`docker-entrypoint.sh`](docker-entrypoint.sh)の自動実行機能を考慮した最適な手順を示しています。

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
