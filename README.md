# FastAPI エンタープライズアプリケーション基盤 (KOIKI-FW)

これは、Python (FastAPI) を用いたエンタープライズ向けWebアプリケーション構築のための、堅牢な基盤フレームワーク「KOIKI-FW」をベースにしたプロジェクトテンプレートです。

現在は `v0.7.0` として、バックエンドを `components/libkoiki` と `components/koiki_ref_app` を中心とした構成へ整理しています。

詳細は `docs/design_kkfw_0.7.0.md` と `docs/dev/` 配下の保守タスク記録を参照してください。

## 特徴

*   **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery, structlog, Prometheus, slowapi 等。
*   **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離。
*   **非同期処理**: 高パフォーマンスな非同期処理。
*   **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上。
*   **テスト容易性**: 依存性注入による容易なテスト実装。
*   **v0.7.0 構成整理**: reusable framework (`components/libkoiki`) と reference application (`components/koiki_ref_app`) の責務を明確化。
*   **認証・セキュリティ基盤**: JWT認証, リフレッシュトークン, パスワードリセット, ログイン試行制限, RBAC, レートリミット等。
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
- `components/koiki_ref_app/alembic/versions` ディレクトリの確認と作成
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
./ops/scripts/run_tests.sh test

# 初回実行（セットアップ付き）
./ops/scripts/run_tests.sh setup

# ヘルプ表示
./ops/scripts/run_tests.sh help
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
- クイックガイド: `docs/testing/QUICK_TEST_GUIDE.md`
- 詳細なテスト手順: `ops/README.md`

### ローカルでのテスト実行

```bash
# 依存関係の同期
uv sync

# カバレッジレポート付きでテスト実行
uv run pytest --cov=koiki_ref_app --cov=libkoiki --cov-report=term-missing \
  components/libkoiki/tests/ \
  components/koiki_ref_app/tests/ \
  tests/unit/agent_guidance/ \
  tests/integration/services/
```

### 継続的インテグレーション (CI)

GitHub Actionsによる自動テストパイプラインが設定されており、以下のブランチへのプッシュ時に自動実行されます：
- `main`
- `dev/v0.7`
- `support/0.6`
- `topic/*`
- `feature/*`

プルリクエスト時にも自動的にテストが実行され、コードの品質が検証されます。

## ディレクトリ構造

```
プロジェクトルート/
├── app/                              # 互換 wrapper (`app.main:app`) を維持する薄い層
├── apps/                             # downstream 案件固有アプリの配置先
├── components/
│   ├── libkoiki/
│   │   ├── src/libkoiki/             # 再利用可能なバックエンドフレームワーク
│   │   └── tests/                    # framework 所有テスト
│   └── koiki_ref_app/
│       ├── src/koiki_ref_app/        # 参照アプリ兼 backend starter
│       ├── alembic/                  # 参照アプリ所有マイグレーション
│       └── tests/                    # ref app 所有テスト
├── frontend/                         # root 配置の starter frontend
├── tests/                            # root 共有テスト / e2e / agent guidance
├── .env.example             # 環境変数サンプル
├── .github/                 # GitHub Actions設定
├── docker-compose.yml       # Docker構成
├── Dockerfile               # コンテナイメージ定義
└── README.md                # プロジェクト説明
```

**注意**:
- 現在の主な実装は `components/libkoiki` と `components/koiki_ref_app` にあります。
- root `app/` は互換導線を維持するための wrapper です。
- `apps/` は downstream の案件固有コードのための予約領域です。

詳細な構成と機能説明は `docs/design_kkfw_0.7.0.md` を参照してください。

## 🔒 Fork・利用に関するご案内

このリポジトリはパブリック公開されていますが、以下の条件を遵守いただける方以外の Fork・再利用はご遠慮ください。

- Fork の前に、必ずリポジトリ管理者（@zaziedlm）にご連絡ください

無断でのForkや再利用が確認された場合、GitHubへの削除申請を行うことがあります。ご理解とご協力をお願いします。

## ライセンス

MIT License

https://opensource.org/license/mit
