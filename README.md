# FastAPI エンタープライズアプリケーション基盤 (KOIKI-FW v0.5.0)

これは、Python (FastAPI) を用いたエンタープライズ向けWebアプリケーション構築のための、堅牢な基盤フレームワーク「KOIKI-FW」の v0.5.0 をベースにしたプロジェクトテンプレートです。

詳細は `docs/design_kkfw_0.5.0.md` ドキュメントを参照してください。

## 特徴

*   **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery, structlog, Prometheus, slowapi 等。
*   **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離。
*   **非同期処理**: 高パフォーマンスな非同期処理。
*   **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上。
*   **テスト容易性**: 依存性注入による容易なテスト実装。
*   **セキュリティ**: JWT認証, RBAC, レートリミット, セキュリティヘッダ等の基本機能。
*   **監視・ロギング**: 構造化ログ, 監査ログ, Prometheus連携。
*   **継続的インテグレーション**: GitHub Actionsによる自動テスト、コード品質チェックの導入。

## セットアップと実行 (Docker Compose)

### 初回環境構築

```bash
# 環境変数ファイルの準備
cp .env.example .env
# 必要に応じて.envファイルを編集

# コンテナのビルドと起動
docker-compose up --build -d
```

上記コマンドにより、以下が自動的に実行されます：
- データベース接続の確認（最大30回リトライ）
- alembic/versionsディレクトリの確認と作成
- 初期マイグレーション実行

### アプリケーションログの確認

```bash
# アプリケーション起動ログの確認
docker-compose logs -f app
```

### アプリケーションへのアクセス

*   API ドキュメント (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
*   API ドキュメント (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)
*   ルートエンドポイント: [http://localhost:8000/](http://localhost:8000/)
## テストの実行

### ローカルでのテスト実行

```bash
# Poetryを使用したテスト実行
poetry run pytest

# カバレッジレポート付きでテスト実行
poetry run pytest --cov=app --cov=libkoiki --cov-report=term-missing tests/
```

### 継続的インテグレーション (CI)

GitHub Actionsによる自動テストパイプラインが設定されており、以下のブランチへのプッシュ時に自動実行されます：
- master
- develop
- dev/*
- feature/*
- bugfix/*

プルリクエスト時にも自動的にテストが実行され、コードの品質が検証されます。

## ディレクトリ構造

```
プロジェクトルート/
├── app/                     # アプリケーション固有のコード
│   ├── api/                 # アプリケーション固有のDIなど
│   ├── models/              # アプリケーション固有のDBモデル
│   ├── repositories/        # アプリケーション固有のリポジトリ
│   ├── routers/             # アプリケーション固有のAPIルーター
│   ├── schemas/             # アプリケーション固有のPydanticスキーマ
│   ├── services/            # アプリケーション固有のサービス
│   └── main.py              # アプリケーションのエントリポイント
├── libkoiki/                # フレームワークコアライブラリ
│   ├── api/                 # API共通コンポーネント
│   ├── core/                # コアユーティリティ (設定・認証・ロギングなど)
│   ├── db/                  # データベース関連
│   ├── models/              # 共通DBモデル (User, Role, Permissionなど)
│   ├── repositories/        # 共通リポジトリ
│   ├── schemas/             # 共通Pydanticスキーマ
│   ├── services/            # 共通サービス
│   └── tasks/               # Celeryタスク関連
├── alembic/                 # DBマイグレーションスクリプト
├── tests/                   # テストコード (unit, integration)
├── .env.example             # 環境変数サンプル
├── .github/                 # GitHub Actions設定
├── docker-compose.yml       # Docker構成
├── Dockerfile               # コンテナイメージ定義
└── README.md                # プロジェクト説明
```

詳細な構成と機能説明は `docs/design_kkfw_0.5.0.md` を参照してください。

## ライセンス

MIT License

https://opensource.org/license/mit
