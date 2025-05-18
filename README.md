# FastAPI エンタープライズアプリケーション基盤 (KOIKI-FW v0.3.0)

これは、Python (FastAPI) を用いたエンタープライズ向けWebアプリケーション構築のための、堅牢な基盤フレームワーク「KOIKI-FW」の v0.3.0 をベースにしたプロジェクトテンプレートです。

詳細は `docs/KOIKI-FW_0.3.0.md` ドキュメントを参照してください。

## 特徴

*   **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery, structlog, Prometheus, slowapi 等。
*   **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離。
*   **非同期処理**: 高パフォーマンスな非同期処理。
*   **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上。
*   **テスト容易性**: 依存性注入による容易なテスト実装。
*   **セキュリティ**: JWT認証, RBAC, レートリミット, セキュリティヘッダ等の基本機能。
*   **監視・ロギング**: 構造化ログ, 監査ログ, Prometheus連携。

## セットアップと実行 (Docker Compose)


X.  **アプリケーションへのアクセス:**
     *   API ドキュメント (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
    *   API ドキュメント (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)
    *   ルートエンドポイント: [http://localhost:8000/](http://localhost:8000/)
## テストの実行


## ディレクトリ構造

(省略 - KOIKI-FW_0.3.0.md または上記のファイル構成概要を参照)

## ライセンス

MIT License