# KOIKI-FW アーキテクチャ構造

## 基本構造
```
プロジェクトルート/
├── components/
│   ├── libkoiki/            # reusable framework package
│   └── koiki_ref_app/       # reference application package
├── app/                     # compatibility wrapper
├── tests/                   # root-level shared / integration tests
├── docs/                    # プロジェクトドキュメント
└── ops/                     # 運用・テストスクリプト
```

## components/libkoiki フレームワーク
- **`src/libkoiki/core/`**: 設定、ログ、セキュリティ、ミドルウェア、エラーハンドリング + 認証デコレーター
- **`src/libkoiki/api/v1/endpoints/`**: モジュラーAPIエンドポイント
  - 認証系: `auth.py`, `auth_basic.py`, `auth_password.py`, `auth_token.py`
  - セキュリティ: `security_monitor.py` (v0.6.0新機能)
  - 機能系: `users.py`, `todos.py`
- **`src/libkoiki/models/`**: SQLAlchemy ORMモデル
  - コア: `User`, `Todo`, `Role`, `Permission`
  - v0.6.0認証: `RefreshTokenModel`, `LoginAttemptModel`, `PasswordResetModel`
- **`src/libkoiki/repositories/`**: データアクセス層（Repository パターン）
- **`src/libkoiki/services/`**: ビジネスロジック層
  - v0.6.0認証: `AuthService`, `PasswordResetService`, `LoginSecurityService`
- **`src/libkoiki/schemas/`**: Pydantic バリデーションモデル
- **`src/libkoiki/db/`**: データベースセッション管理
- **`src/libkoiki/events/`**: イベント配信・ハンドリング（Redis-based）
- **`src/libkoiki/tasks/`**: Celeryタスク定義
- **`src/libkoiki/utils/`**: ユーティリティ関数

## components/koiki_ref_app 参照アプリケーション
- libkoikiを基盤とした reference app 実装用
- app 固有 bootstrap、SSO/SAML、todo などの参照ドメインを持つ
- ASGI 正本は `koiki_ref_app.asgi:app`

## app ディレクトリ
- 旧 `app.main:app` 向けの互換 wrapper
- 新規実装の正本として扱わない

## アーキテクチャパターン
- **レイヤードアーキテクチャ**: API → サービス → リポジトリ → モデル
- **依存性注入**: FastAPIのDI システムを広範囲に活用
- **Repository パターン**: データアクセスの抽象化
- **イベント駆動**: 非同期イベントハンドリング（Redis-based、現在無効）
