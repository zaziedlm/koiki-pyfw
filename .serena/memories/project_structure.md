# プロジェクト構造

## ルートディレクトリ構成

```
koiki-pyfw/
├── .editorconfig          # エディタ設定（統一フォーマット）
├── .env.example           # 環境変数テンプレート
├── .gitignore            # Git除外ファイル設定
├── .python-version-sample # Python バージョン指定
├── pyproject.toml        # Poetry プロジェクト設定・依存関係管理
├── poetry.lock           # 依存関係バージョン固定
├── alembic.ini           # データベースマイグレーション設定
├── docker-compose.yml    # 開発環境Docker設定
├── Dockerfile            # アプリケーションDocker設定
├── main.py              # メインエントリーポイント
├── start-local-dev.ps1  # Windows開発用起動スクリプト
├── run_security_test.sh # セキュリティテスト実行スクリプト
├── README.md            # プロジェクトメインドキュメント
├── QUICK_TEST_GUIDE.md  # テスト実行クイックガイド
└── 認証系APIテストガイド.md # 認証APIの詳細ガイド
```

## メインディレクトリ詳細

### libkoiki/ - フレームワークコア（再利用可能）

```
libkoiki/
├── __init__.py
├── pyproject.toml           # libkoiki専用設定
├── api/                     # API関連モジュール
│   ├── dependencies.py      # 依存性注入定義（DB、Redis、サービス等）
│   └── v1/                  # APIバージョン1
│       ├── endpoints/       # RESTエンドポイント実装
│       │   ├── auth_basic.py    # 基本認証API
│       │   ├── auth_password.py # パスワード管理API
│       │   ├── auth_token.py    # トークン管理API
│       │   ├── users.py         # ユーザー管理API
│       │   ├── todos.py         # タスク管理API
│       │   └── security_monitor.py # セキュリティ監視API
│       └── router.py        # APIルーター設定
├── core/                    # フレームワークコア機能
│   ├── config.py           # 設定管理クラス（Pydantic Settings）
│   ├── security.py         # JWT認証・パスワード暗号化
│   ├── security_config.py  # セキュリティ設定管理
│   ├── security_logger.py  # セキュリティログ専用
│   ├── security_metrics.py # セキュリティメトリクス収集
│   ├── exceptions.py       # カスタム例外定義
│   ├── error_handlers.py   # 例外ハンドラー設定
│   ├── logging.py          # 構造化ログ設定（structlog）
│   ├── middleware.py       # リクエスト・セキュリティミドルウェア
│   ├── monitoring.py       # Prometheusメトリクス
│   ├── rate_limiter.py     # レートリミット設定
│   └── transaction.py      # トランザクション管理デコレータ
├── db/                     # データベース関連
│   ├── base.py            # SQLAlchemyベースモデル
│   └── session.py         # 非同期セッション管理
├── models/                 # SQLAlchemyモデル（データベーステーブル）
│   ├── user.py            # ユーザーモデル
│   ├── todo.py            # タスクモデル
│   ├── role.py            # ロールモデル（RBAC）
│   ├── permission.py      # 権限モデル（RBAC）
│   ├── refresh_token.py   # リフレッシュトークンモデル
│   ├── password_reset.py  # パスワードリセットトークンモデル
│   ├── login_attempt.py   # ログイン試行記録モデル
│   └── associations.py    # 多対多関連テーブル定義
├── repositories/           # データアクセス層（Repository パターン）
│   ├── base.py            # ベースリポジトリクラス
│   ├── user_repository.py
│   ├── todo_repository.py
│   ├── refresh_token_repository.py
│   ├── password_reset_repository.py
│   └── login_attempt_repository.py
├── schemas/               # Pydanticスキーマ（API I/O）
│   ├── user.py           # ユーザー関連スキーマ
│   ├── todo.py           # タスク関連スキーマ
│   ├── auth.py           # 認証関連スキーマ
│   ├── token.py          # トークン関連スキーマ
│   ├── role.py           # ロール関連スキーマ
│   ├── permission.py     # 権限関連スキーマ
│   └── refresh_token.py  # リフレッシュトークン関連スキーマ
├── services/              # ビジネスロジック層
│   ├── user_service.py           # ユーザー管理ビジネスロジック
│   ├── todo_service.py           # タスク管理ビジネスロジック
│   ├── auth_service.py           # 認証ビジネスロジック
│   ├── password_reset_service.py # パスワードリセットロジック
│   └── login_security_service.py # ログインセキュリティロジック
├── tasks/                 # 非同期タスク（Celery）
│   ├── celery_app.py     # Celeryアプリケーション設定
│   └── email.py          # メール送信タスク
├── events/               # イベントドリブン処理
│   ├── publisher.py      # イベント発行（Redis Pub/Sub）
│   └── handlers.py       # イベントハンドラー
└── utils/                # ユーティリティ関数
    └── email.py          # メール送信ユーティリティ
```

### app/ - アプリケーション固有実装

```
app/
├── main.py               # FastAPIアプリケーション定義・起動設定
└── api/
    └── dependencies.py   # アプリケーション固有の依存性注入
```

### frontend/ - Next.js + TypeScript フロントエンド（NEW）

```
frontend/
├── package.json          # Node.js依存関係・スクリプト定義
├── tsconfig.json         # TypeScript設定
├── next.config.ts        # Next.js設定
├── eslint.config.mjs     # ESLint設定
├── components.json       # shadcn/ui設定
├── middleware.ts         # Next.js ミドルウェア
├── public/              # 静的ファイル
├── src/
│   ├── app/             # App Router（Next.js 13+）
│   │   ├── layout.tsx   # ルートレイアウト
│   │   ├── page.tsx     # ホームページ
│   │   ├── auth/        # 認証関連ページ
│   │   │   ├── login/
│   │   │   └── register/
│   │   └── dashboard/   # ダッシュボード
│   │       └── tasks/   # タスク管理ページ
│   ├── components/      # 再利用可能コンポーネント
│   │   ├── ui/         # 基本UIコンポーネント（shadcn/ui）
│   │   ├── auth/       # 認証関連コンポーネント
│   │   ├── layout/     # レイアウトコンポーネント
│   │   ├── tasks/      # タスク管理コンポーネント
│   │   └── providers/  # Context プロバイダー
│   ├── hooks/          # カスタムReact Hooks
│   │   ├── use-auth-queries.ts    # 認証関連クエリ
│   │   ├── use-todo-queries.ts    # タスククエリ
│   │   ├── use-user-queries.ts    # ユーザークエリ
│   │   └── use-security-queries.ts # セキュリティクエリ
│   ├── lib/            # ユーティリティ・設定
│   │   ├── api-client.ts    # APIクライアント設定
│   │   ├── config.ts        # アプリケーション設定
│   │   ├── react-query.tsx  # React Query設定
│   │   ├── token-utils.ts   # トークン管理ユーティリティ
│   │   └── utils.ts         # 汎用ユーティリティ
│   ├── stores/         # 状態管理（Zustand）
│   │   ├── auth-store.ts      # 認証状態
│   │   ├── todo-store.ts      # タスク状態
│   │   ├── user-store.ts      # ユーザー状態
│   │   ├── security-store.ts  # セキュリティ状態
│   │   └── ui-store.ts        # UI状態
│   └── types/          # TypeScript型定義
│       ├── api.ts      # API関連型
│       ├── auth.ts     # 認証関連型
│       ├── todo.ts     # タスク関連型
│       ├── user.ts     # ユーザー関連型
│       └── security.ts # セキュリティ関連型
```

### tests/ - 包括的テスト戦略

```
tests/
├── conftest.py           # pytest設定・共通フィクスチャ
├── unit/                # 単体テスト（モック使用）
│   ├── app/services/    # アプリケーション固有サービステスト
│   └── libkoiki/        # フレームワークコアテスト
│       └── services/    # サービス層単体テスト
├── integration/         # 統合テスト（実データベース使用）
│   ├── app/api/        # APIエンドポイント統合テスト
│   └── services/       # サービス層統合テスト
└── local/              # ローカル環境専用テスト
```

### docs/ - プロジェクトドキュメント

```
docs/
├── design_kkfw_0.6.0.md         # 詳細設計ドキュメント（3474行）
├── authentication-api-guide.md  # 認証APIガイド
├── architecture.md              # システムアーキテクチャ
└── dev/                        # 開発者向けドキュメント
    ├── setup.md
    └── deploy.md
```

### ops/ - 運用・セキュリティ管理

```
ops/
├── README.md             # 運用ガイド
├── Makefile             # 運用タスク自動化
├── scripts/             # 運用スクリプト
│   ├── security_test_manager.sh  # セキュリティテスト管理
│   └── setup_security.py         # セキュリティ設定セットアップ
├── security/            # セキュリティ設定ファイル
└── tests/              # 運用テスト
    └── test_security_api.py      # セキュリティAPI統合テスト
```

### alembic/ - データベースマイグレーション

```
alembic/
├── env.py               # Alembic環境設定
├── script.py.mako       # マイグレーションテンプレート
└── versions/           # マイグレーションファイル
    ├── 168fc6abc982_initial_migration.py
    ├── 2025070702_add_refresh_tokens_table.py
    └── ... （その他のマイグレーション）
```

## 設定・CI/CD

### GitHub Actions
```
.github/
└── workflows/
    └── ci.yml           # 自動テスト・品質チェックパイプライン
```

### VS Code設定
```
.vscode/
└── mcp.json           # Model Context Protocol設定
```