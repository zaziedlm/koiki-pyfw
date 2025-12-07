# プロジェクト構造

## ディレクトリ概要

```
├── app/                    # アプリケーション固有コード
│   ├── api/v1/endpoints/   # SSO/SAML認証、ビジネスAPI
│   ├── core/               # SSO/SAML設定
│   ├── models/             # アプリ固有モデル（UserSSO, BusinessClock等）
│   ├── repositories/       # アプリ固有リポジトリ
│   ├── schemas/            # アプリ固有スキーマ
│   ├── services/           # SSO/SAMLサービス
│   └── main.py             # アプリケーションエントリポイント
│
├── libkoiki/               # フレームワークコアライブラリ
│   ├── api/v1/endpoints/   # 認証、ユーザー、Todo、セキュリティ監視API
│   ├── core/               # 設定、セキュリティ、ミドルウェア、ログ
│   ├── db/                 # DBセッション管理
│   ├── models/             # User, Role, Permission, Todo, RefreshToken等
│   ├── repositories/       # データアクセス層
│   ├── schemas/            # Pydanticスキーマ
│   ├── services/           # AuthService, UserService, TodoService等
│   ├── events/             # イベントパブリッシャー/ハンドラー
│   └── tasks/              # Celeryタスク
│
├── frontend/               # Next.js フロントエンド
│   └── src/
│       ├── app/            # App Router（ページ、API Routes）
│       │   ├── api/        # Route Handlers（バックエンドプロキシ）
│       │   ├── auth/       # 認証ページ
│       │   ├── dashboard/  # ダッシュボード
│       │   └── sso/        # SSOコールバック
│       ├── components/     # UIコンポーネント
│       ├── hooks/          # カスタムフック（認証、Todo、SSO）
│       ├── lib/            # ユーティリティ（API client、CSRF、Cookie）
│       ├── stores/         # Zustand状態管理
│       └── types/          # TypeScript型定義
│
├── alembic/                # DBマイグレーション
├── tests/                  # テスト（unit/integration）
├── ops/                    # 運用スクリプト、セキュリティテスト
├── docker/                 # Docker関連（証明書、Keycloak設定）
└── docs/                   # ドキュメント
```

## 階層アーキテクチャ

```
API層 (endpoints)
    ↓ 依存性注入
Service層 (services)
    ↓ ビジネスロジック
Repository層 (repositories)
    ↓ データアクセス
Model層 (models) + DB
```

## libkoiki vs app の役割分担

| 機能 | libkoiki | app |
|------|----------|-----|
| JWT認証 | ✅ | - |
| ユーザー管理 | ✅ | - |
| Todo管理 | ✅ | - |
| RBAC | ✅ | - |
| SSO/OIDC | - | ✅ |
| SAML認証 | - | ✅ |
| ビジネスロジック | - | ✅ |

## フロントエンド統合パターン

```
ユーザー操作
    ↓
React Component
    ↓
TanStack Query Hook (use-cookie-auth-queries.ts等)
    ↓
Cookie API Client (cookie-api-client.ts)
    ↓
Next.js Route Handler (/api/auth/login等)
    ↓
FastAPI Backend (/api/v1/auth/login)
```

## 主要ファイル

- `app/main.py`: アプリケーション起動、ミドルウェア設定
- `libkoiki/core/config.py`: 環境変数ベースの設定管理
- `libkoiki/core/security.py`: JWT認証、パスワード処理
- `frontend/src/middleware.ts`: 認証ガード
- `frontend/src/lib/cookie-api-client.ts`: CSRF対応APIクライアント
