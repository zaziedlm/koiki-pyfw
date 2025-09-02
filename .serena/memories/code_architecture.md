# KOIKI-FW アーキテクチャ構造

## 基本構造
```
プロジェクトルート/
├── app/                     # アプリケーション固有のコード (拡張用)
├── libkoiki/                # フレームワークコアライブラリ (主要機能実装済み)
├── alembic/                 # DBマイグレーションスクリプト
├── tests/                   # テストコード (unit, integration)
├── docs/                    # プロジェクトドキュメント
└── ops/                     # 運用・テストスクリプト
```

## libkoiki フレームワーク（メイン実装）
- **`core/`**: 設定、ログ、セキュリティ、ミドルウェア、エラーハンドリング + 認証デコレーター
- **`api/v1/endpoints/`**: モジュラーAPIエンドポイント
  - 認証系: `auth.py`, `auth_basic.py`, `auth_password.py`, `auth_token.py`
  - セキュリティ: `security_monitor.py` (v0.6.0新機能)
  - 機能系: `users.py`, `todos.py`
- **`models/`**: SQLAlchemy ORMモデル
  - コア: `User`, `Todo`, `Role`, `Permission`
  - v0.6.0認証: `RefreshTokenModel`, `LoginAttemptModel`, `PasswordResetModel`
- **`repositories/`**: データアクセス層（Repository パターン）
- **`services/`**: ビジネスロジック層
  - v0.6.0認証: `AuthService`, `PasswordResetService`, `LoginSecurityService`
- **`schemas/`**: Pydantic バリデーションモデル
- **`db/`**: データベースセッション管理
- **`events/`**: イベント配信・ハンドリング（Redis-based）
- **`tasks/`**: Celeryタスク定義
- **`utils/`**: ユーティリティ関数

## app ディレクトリ（拡張レイヤー）
- libkoikiを基盤とした、アプリケーション固有の実装用
- 同じレイヤードアーキテクチャパターンに従う
- `main.py`: アプリケーションエントリポイント

## アーキテクチャパターン
- **レイヤードアーキテクチャ**: API → サービス → リポジトリ → モデル
- **依存性注入**: FastAPIのDI システムを広範囲に活用
- **Repository パターン**: データアクセスの抽象化
- **イベント駆動**: 非同期イベントハンドリング（Redis-based、現在無効）