# KOIKI-FW プロジェクト概要

## プロジェクトの目的
KOIKI-FW v0.6.0は、Python FastAPIを使ったエンタープライズ向けWebアプリケーション構築のための堅牢な基盤フレームワークです。

## 主な特徴
- **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery等
- **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離  
- **非同期処理**: 高パフォーマンスな非同期処理
- **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上
- **v0.6.0強化されたセキュリティ**: JWT認証, リフレッシュトークン, パスワードリセット, ログイン試行制限, RBAC等
- **v0.6.0認証系API**: modular認証システム（基本認証、パスワード管理、トークン管理）
- **監視・ロギング**: 構造化ログ, 監査ログ, Prometheus連携

## アクセスポイント
- API ドキュメント (Swagger UI): http://localhost:8000/docs
- API ドキュメント (ReDoc): http://localhost:8000/redoc
- ルートエンドポイント: http://localhost:8000/