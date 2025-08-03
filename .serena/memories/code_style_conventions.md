# KOIKI-FW コードスタイル・規約

## 言語・バージョン
- **Python**: >=3.11.7,<4.0
- **型ヒント**: 必須（Pydantic v2使用）
- **非同期**: async/await パターン採用

## パッケージ構成
- **PEP 621準拠**: pyproject.tomlの[project]セクションでメタデータ管理
- **Poetry 2.x**: 依存関係管理、dependency groups活用
- **セマンティックバージョニング**: メジャー.マイナー.パッチ形式

## アーキテクチャパターン
- **レイヤードアーキテクチャ**: API → Service → Repository → Model
- **依存性注入**: FastAPIのDIシステム活用
- **Repository パターン**: データアクセスの抽象化
- **BaseRepository継承**: 共通CRUD操作の統一

## 命名規約
- **ファイル**: snake_case (`user_service.py`)
- **クラス**: PascalCase (`UserService`)
- **関数・変数**: snake_case (`get_current_user`)
- **定数**: UPPER_SNAKE_CASE (`REDIS_AVAILABLE`)
- **モデル**: `*Model` suffix (`UserModel`)
- **スキーマ**: 目的別suffix (`UserCreate`, `UserResponse`)
- **リポジトリ**: `*Repository` suffix (`UserRepository`)
- **サービス**: `*Service` suffix (`UserService`)

## ログ・エラーハンドリング
- **structlog**: 構造化ログ使用
- **logger変数**: 各モジュールでget_logger(__name__)
- **例外**: カスタム例外クラス継承（BaseAppException）
- **セキュリティログ**: 認証・認可イベントの詳細ログ

## 設定・環境変数
- **pydantic-settings**: 設定管理
- **環境変数**: 大文字アンダースコア（DATABASE_URL）
- **.env**: ローカル開発用設定
- **階層設定**: 環境変数 → .env → デフォルト

## テスト
- **pytest**: 非同期テスト（pytest-asyncio）
- **テスト構造**: tests/{unit,integration}/{app,libkoiki}/
- **命名**: test_*.py、test_*関数
- **モック**: pytest-mock使用
- **カバレッジ**: --cov オプション