# プロジェクト構造・組織

## アーキテクチャ概要

KOIKI-FWは、フレームワークコア（`libkoiki/`）とアプリケーション固有コード（`app/`）を明確に分離した**階層アーキテクチャ**に従います。この設計により、再利用性、保守性を促進し、エンタープライズ標準を維持しながら迅速な開発を可能にします。

## ディレクトリ構造

### ルートレベル
```
├── app/                     # アプリケーション固有の拡張
├── libkoiki/               # フレームワークコアライブラリ（事前実装済み機能）
├── frontend/               # Next.js Reactアプリケーション
├── alembic/               # データベースマイグレーション
├── tests/                 # テストスイート（ユニット・統合）
├── ops/                   # 運用、セキュリティテスト、デプロイスクリプト
├── docs/                  # ドキュメント
├── docker/                # Docker関連ファイル
├── .github/               # CI/CDワークフロー
├── .kiro/                 # Kiro IDE設定
└── .env*                  # 環境設定ファイル
```

## コアディレクトリ

### libkoiki/（フレームワークコア）
**目的**: 事前実装済みエンタープライズ機能と共通機能を含む

```
libkoiki/
├── api/                   # API層コンポーネント
│   └── v1/               # APIバージョン1ルート
├── core/                 # コアユーティリティ
│   ├── config.py         # 設定管理
│   ├── dependencies.py   # 依存性注入
│   ├── security.py       # 認証・認可
│   ├── logging.py        # 構造化ログ設定
│   └── middleware.py     # カスタムミドルウェア
├── db/                   # データベース層
│   ├── base.py          # SQLAlchemyベースクラス
│   └── session.py       # データベースセッション管理
├── models/               # SQLAlchemy ORMモデル
│   ├── user.py          # Userモデル
│   ├── role.py          # Roleモデル
│   ├── permission.py    # Permissionモデル
│   └── todo.py          # Todoモデル（例）
├── repositories/         # データアクセス層
│   ├── base.py          # ベースRepositoryパターン
│   ├── user.py          # UserRepository
│   └── todo.py          # TodoRepository
├── schemas/              # Pydanticスキーマ
│   ├── user.py          # Userスキーマ
│   ├── auth.py          # 認証スキーマ
│   └── todo.py          # Todoスキーマ
├── services/             # ビジネスロジック層
│   ├── auth.py          # 認証Service
│   ├── user.py          # ユーザー管理Service
│   └── todo.py          # TodoService
├── tasks/                # Celery非同期タスク
└── utils/                # ユーティリティ関数
```

### app/（アプリケーション拡張）
**目的**: アプリケーション固有のカスタマイズと拡張

```
app/
├── api/                  # アプリケーション固有APIルート
│   └── v1/              # カスタムAPIエンドポイント
├── core/                # アプリ固有コアユーティリティ
├── models/              # 拡張またはカスタムモデル
├── repositories/        # カスタムRepository実装
├── schemas/             # カスタムPydanticスキーマ
├── services/            # カスタムビジネスロジック
├── main.py              # アプリケーションエントリポイント
└── pyproject.toml       # アプリ固有依存関係
```

### frontend/（Next.jsアプリケーション）
```
frontend/
├── src/
│   ├── app/             # Next.js App Router
│   │   ├── api/         # API Route Handlers（バックエンドプロキシ）
│   │   │   ├── auth/    # 認証API（login, logout, csrf等）
│   │   │   ├── todos/   # TodoAPI プロキシ
│   │   │   └── users/   # ユーザーAPI プロキシ
│   │   ├── auth/        # 認証ページ（login, register）
│   │   ├── dashboard/   # ダッシュボードページ
│   │   └── globals.css  # グローバルスタイル
│   ├── components/      # React components
│   │   ├── auth/        # 認証関連コンポーネント
│   │   ├── layout/      # レイアウトコンポーネント
│   │   ├── tasks/       # タスク管理コンポーネント
│   │   └── ui/          # 基本UIコンポーネント（shadcn/ui）
│   ├── hooks/           # カスタムReactフック
│   │   ├── use-cookie-auth-queries.ts  # Cookie認証フック
│   │   └── use-cookie-todo-queries.ts  # Todo管理フック
│   ├── lib/             # ユーティリティライブラリ
│   │   ├── cookie-api-client.ts  # Cookie認証APIクライアント
│   │   ├── csrf-utils.ts         # CSRF保護ユーティリティ
│   │   ├── cookie-utils.ts       # Cookie管理ユーティリティ
│   │   └── config.ts             # フロントエンド設定
│   ├── stores/          # 状態管理（Zustand）
│   ├── types/           # TypeScript型定義
│   │   ├── api.ts       # API型定義
│   │   ├── auth.ts      # 認証型定義
│   │   └── user.ts      # ユーザー型定義
│   └── middleware.ts    # Next.js Middleware（認証ガード）
├── public/             # 静的アセット
├── package.json        # 依存関係
├── next.config.ts      # Next.js設定
├── tailwind.config.ts  # Tailwind CSS設定
└── components.json     # shadcn/ui設定
```

### tests/（テスト組織）
```
tests/
├── unit/               # ユニットテスト
│   ├── test_models.py
│   ├── test_services.py
│   └── test_repositories.py
├── integration/        # 統合テスト
│   ├── test_api.py
│   └── test_auth.py
└── conftest.py        # Pytest設定
```

### ops/（運用・セキュリティ）
```
ops/
├── scripts/           # デプロイ・ユーティリティスクリプト
├── security/          # セキュリティ設定・テスト
├── tests/            # 運用テスト
└── requirements.txt   # 運用固有依存関係
```

## 階層アーキテクチャパターン

### 1. API層（`api/`）
- **責務**: HTTPリクエスト/レスポンス処理、入力検証、認証
- **コンポーネント**: FastAPIルーター、エンドポイント定義、リクエスト/レスポンスモデル
- **依存関係**: Service層

### 2. Service層（`services/`）
- **責務**: ビジネスロジック、オーケストレーション、トランザクション管理
- **コンポーネント**: Serviceクラス、ビジネスルール、ワークフロー調整
- **依存関係**: Repository層、外部サービス

### 3. Repository層（`repositories/`）
- **責務**: データアクセス抽象化、データベース操作
- **コンポーネント**: Repositoryクラス、クエリビルダー、データマッピング
- **依存関係**: データベースモデル、SQLAlchemyセッション

### 4. Model層（`models/`）
- **責務**: データ構造定義、データベーススキーマ
- **コンポーネント**: SQLAlchemy ORMモデル、データベースリレーション
- **依存関係**: SQLAlchemyベースクラス

## ファイル命名規則

### Pythonファイル
- **Models**: `user.py`、`todo.py`（単数形、小文字）
- **Services**: `user_service.py`、`auth_service.py`（説明的）
- **Repositories**: `user_repository.py`、`base_repository.py`
- **Schemas**: `user_schemas.py`、`auth_schemas.py`
- **APIルート**: `user_router.py`、`auth_router.py`

### フロントエンドファイル
- **Components**: `UserProfile.tsx`、`TodoList.tsx`（PascalCase）
- **Pages**: `login.tsx`、`dashboard.tsx`（小文字）
- **Hooks**: `useAuth.ts`、`useTodos.ts`（camelCaseで'use'プレフィックス）
- **Types**: `user.types.ts`、`api.types.ts`

## インポート規則

### 絶対インポート（推奨）
```python
# libkoikiから
from libkoiki.models.user import User
from libkoiki.services.auth import AuthService
from libkoiki.core.dependencies import get_current_user

# appから
from app.services.custom_service import CustomService
from app.models.custom_model import CustomModel
```

### 相対インポート（同一パッケージ内）
```python
# libkoikiパッケージ内
from .base import BaseRepository
from ..models.user import User
```

## 設定管理

### 環境ファイル
- `.env`: メイン設定（コミット対象外）
- `.env.example`: 全必要変数のテンプレート
- `.env.local`: ローカル開発オーバーライド
- `.env.test`: テスト環境設定

### 設定階層
1. 環境変数
2. `.env`ファイル
3. `config.py`のデフォルト値

## フルスタック統合パターン

### API統合フロー
1. **バックエンドAPI**: libkoiki/api/v1/endpoints/ でAPI実装
2. **フロントエンドプロキシ**: frontend/src/app/api/ でRoute Handler作成
3. **型定義**: frontend/src/types/ でTypeScript型定義
4. **フック**: frontend/src/hooks/ でTanStack Queryフック実装
5. **コンポーネント**: frontend/src/components/ でUI実装

### 認証統合パターン
```typescript
// フロントエンド: middleware.ts
export function middleware(request: NextRequest) {
  // 認証チェック・リダイレクト処理
}

// バックエンド: dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
  # JWT検証・ユーザー取得
```

### データフロー統合
```
ユーザー操作 → React Component → TanStack Query → 
API Route Handler → FastAPI Endpoint → Service → Repository → Database
```

## 拡張ガイドライン

### 新機能追加
1. **コア機能**: アプリケーション間で再利用可能な場合は`libkoiki/`に実装
2. **アプリ固有**: プロジェクト固有機能は`app/`に実装
3. **フロントエンド**: `frontend/src/`に対応するUI実装
4. **層の遵守**: API → Service → Repository → Modelの流れを維持
5. **テスト**: `tests/`ディレクトリに対応するテストを追加

### フルスタック機能追加手順
1. **バックエンド実装**: API、Service、Repository、Modelを実装
2. **フロントエンドプロキシ**: API Route Handlerを作成
3. **型定義**: TypeScript型定義を追加
4. **フック実装**: データ取得・更新フックを作成
5. **UI実装**: コンポーネントとページを実装
6. **統合テスト**: E2Eテストを追加

### データベース変更
1. マイグレーション作成: `alembic revision --autogenerate -m "説明"`
2. 生成されたマイグレーションファイルをレビュー
3. 適用: `alembic upgrade head`
4. バックエンドモデルとスキーマを更新
5. フロントエンド型定義を更新