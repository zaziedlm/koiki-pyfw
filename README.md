# FastAPI エンタープライズアプリケーション基盤 (KOIKI-FW v0.6.0)

これは、Python (FastAPI) を用いたエンタープライズ向けWebアプリケーション構築のための、堅牢な基盤フレームワーク「KOIKI-FW」の v0.6.0 をベースにしたプロジェクトテンプレートです。

詳細は `docs/design_kkfw_0.6.0.md` ドキュメントを参照してください。

## 特徴

*   **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery, structlog, Prometheus, slowapi 等。
*   **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離。
*   **非同期処理**: 高パフォーマンスな非同期処理。
*   **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上。
*   **テスト容易性**: 依存性注入による容易なテスト実装。
*   **🆕 v0.6.0 強化されたセキュリティ**: JWT認証, リフレッシュトークン, パスワードリセット, ログイン試行制限, RBAC, レートリミット等。
*   **🆕 v0.6.0 認証系API**: modular認証システム（基本認証、パスワード管理、トークン管理）。
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

### セキュリティAPIテスト

KOIKI-FWの権限管理システムとセキュリティAPIをテストする場合：

#### 🚀 推奨実行方法（プロジェクトルートから）
```bash
# 環境起動 + テスト実行（ワンコマンド）
./run_security_test.sh test

# 初回実行（セットアップ付き）
./run_security_test.sh setup

# ヘルプ表示
./run_security_test.sh help
```

#### 📋 従来の方法（opsディレクトリから）
```bash
# 環境起動
docker-compose up -d

# セキュリティテスト実行
cd ops
bash scripts/security_test_manager.sh test
```

📚 **詳細情報:**
- クイックガイド: `QUICK_TEST_GUIDE.md`
- 詳細なテスト手順: `ops/README.md`

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
├── app/                     # アプリケーション固有のコード (拡張用)
│   ├── api/                 # アプリケーション固有のDIなど
│   ├── models/              # アプリケーション固有のDBモデル (拡張用)
│   ├── repositories/        # アプリケーション固有のリポジトリ (拡張用)
│   ├── schemas/             # アプリケーション固有のPydanticスキーマ (拡張用)
│   ├── services/            # アプリケーション固有のサービス (拡張用)
│   └── main.py              # アプリケーションのエントリポイント
├── libkoiki/                # フレームワークコアライブラリ (主要機能実装済み)
│   ├── api/                 # API共通コンポーネント
│   ├── core/                # コアユーティリティ (設定・認証・ロギングなど)
│   ├── db/                  # データベース関連
│   ├── models/              # 共通DBモデル (User, Role, Permission, Todo等)
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

**注意**: v0.6.0 では、主要機能（認証、Todo、ユーザー管理）は `libkoiki/` 内に実装されており、`app/` は将来的な拡張用の基盤を提供しています。

詳細な構成と機能説明は `docs/design_kkfw_0.6.0.md` を参照してください。

## 🔒 Fork・利用に関するご案内

このリポジトリは~~パブリック公開されていますが~~、以下の方以外による Fork・再利用はご遠慮ください。

- Fork にあたり指定された、GitHub Enterprise Organization に所属する関係者
- Fork の前に、必ずリポジトリ管理者（@zaziedlm）にご連絡ください

無断でのForkや再利用が確認された場合、GitHubへの削除申請を行うことがあります。ご理解とご協力をお願いします。

## ライセンス

MIT License

https://opensource.org/license/mit
