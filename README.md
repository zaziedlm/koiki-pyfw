# FastAPI エンタープライズアプリケーション基盤 + ToDo サンプル (KOIKI-FW v0.3.0)

これは、Python (FastAPI) を用いたエンタープライズ向けWebアプリケーション構築のための、堅牢な基盤フレームワーク「KOIKI-FW」の v0.3.0 をベースにしたプロジェクトテンプレートです。フレームワークの基本的な使い方を示すためのシンプルな **ToDo アプリケーション** が実装されています。

詳細は `docs/KOIKI-FW_0.3.0.md` ドキュメントを参照してください。

## 特徴

*   **モダンな技術スタック**: FastAPI, SQLAlchemy (Async), Pydantic, Redis, Celery, structlog, Prometheus, slowapi 等。
*   **関心事の分離**: API層、サービス層、リポジトリ層の明確な分離。
*   **非同期処理**: 高パフォーマンスな非同期処理。
*   **型安全性**: Pydantic と型ヒントによる開発効率と安全性の向上。
*   **テスト容易性**: 依存性注入による容易なテスト実装。
*   **セキュリティ**: JWT認証, RBAC, レートリミット, セキュリティヘッダ等の基本機能。
*   **監視・ロギング**: 構造化ログ, 監査ログ, Prometheus連携。
*   **ToDo サンプル**: フレームワークの具体的な利用例としてToDoアプリを実装。

## セットアップと実行 (Docker Compose)

1.  **リポジトリのクローン:**
    ```bash
    git clone <your-repo-url>
    cd KOIKI-FW_TODO_APP
    ```

2.  **環境設定ファイルの作成:**
    `.env.example` をコピーして `.env` ファイルを作成し、必要に応じて設定値を編集します。特に `SECRET_KEY` はランダムな文字列に変更してください。
    ```bash
    cp .env.example .env
    # nano .env または vim .env などで SECRET_KEY を編集
    ```
    *Linux/macOS でのランダムキー生成例:*
    ```bash
    openssl rand -hex 32 >> .env # SECRET_KEY=... の行をこれで置き換えるか、生成されたキーをコピー
    ```

3.  **Docker コンテナのビルドと起動:**
    ```bash
    docker-compose up --build -d
    ```
    これにより、FastAPI アプリケーション、PostgreSQL データベース、Redis、Celery Worker が起動します。

4.  **データベースマイグレーションの適用:**
    最初の起動時やモデル変更後は、マイグレーションを実行してデータベーススキーマを更新する必要があります。
    ```bash
    # コンテナ内で Alembic コマンドを実行
    docker-compose exec app alembic upgrade head
    ```
    *(モデルを変更した場合は、先に `docker-compose exec app alembic revision --autogenerate -m "Your migration message"` を実行してマイグレーションファイルを生成してください)*

5.  **アプリケーションへのアクセス:**
    *   API ドキュメント (Swagger UI): [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
    *   API ドキュメント (ReDoc): [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
    *   ルートエンドポイント: [http://localhost:8000/](http://localhost:8000/)

## ToDo サンプルアプリケーションの使い方

1.  **ユーザー登録:** `/api/v1/users/` エンドポイント (POST) で新しいユーザーを作成します。
2.  **ログイン:** `/api/v1/auth/login` エンドポイント (POST) でユーザー名（メールアドレス）とパスワードを送信し、JWT アクセストークンを取得します。
3.  **トークンの利用:** API ドキュメント画面右上の "Authorize" ボタンをクリックし、取得したトークンを `Bearer <token>` の形式で入力します。
4.  **ToDo 操作:** `/api/v1/todos/` 以下のエンドポイントを使って、認証済みユーザーとして ToDo の作成、一覧取得、更新、削除を行います。

## テストの実行


## ディレクトリ構造

(省略 - KOIKI-FW_0.2.md または上記のファイル構成概要を参照)

## ライセンス

MIT License