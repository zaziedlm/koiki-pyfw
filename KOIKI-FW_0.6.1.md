# KOIKI-FW v0.6.1 技術仕様書

## 概要

KOIKI-FW v0.6.1 は、0.6.0 で導入した認証・監査基盤を安定運用するためのリファクタリングリリースです。エラーハンドリングと構造化ログを整理し、リクエストコンテキストを用いた監査ログ出力と権限チェックの一貫性を強化しました。また、Dependabot 設定や gitignore の整備によって運用・開発体験も向上させています。

## v0.6.1 主要変更点

### コア例外処理とログ整備
- FastAPI / SQLAlchemy の例外ハンドラーを再構成し、structlog ロガーに統一（`libkoiki/core/error_handlers.py`）。
- RequestValidationError のレスポンスをサニタイズして返却し、リクエスト情報とともに記録。
- DB 例外専用ハンドラーを新設し、IntegrityError / NoResultFound に応じて適切な HTTP ステータスとエラーコードを返却。
- 例外ハンドラー登録処理 `setup_exception_handlers` を更新し、JSON レスポンス整合性と監査ログ連携を確保。

### ミドルウェアと監査基盤
- `RequestContextLogMiddleware` を追加し、リクエスト ID・クライアント情報を structlog のコンテキストにバインド。
- 監査ログ対象からヘルスチェックやドキュメント等を除外し、ノイズを削減（`AuditLogMiddleware`）。
- `AccessLogMiddleware` を整理し、処理時間・ステータスコードを構造化ログとして出力。
- セキュリティヘッダー付与処理のガイダンスコメントを整備し、適用順序の明示性を向上。

### 認証・認可依存関係
- `get_current_user_from_token` の戻り値をユーザー ID に限定し、DB アクセスとの責務分離を徹底（`libkoiki/api/dependencies.py`）。
- `get_current_active_user` がロール・パーミッションを再取得し、未ロード時に自動補完。
- RBAC 用 `has_permission` が不足ロール情報を補完し、権限チェックと監査ログの整合性を強化。

### API エンドポイント
- Users / Todos ルーターのベースパスを空文字列に変更し、`/users` / `/todos` での二重スラッシュ問題を解消（`libkoiki/api/v1/endpoints/`）。
- slowapi のレートリミット設定を見直し、Request 依存性を明示して監査ログと整合。

### 運用・DevOps
- Dependabot 設定を追加し、Poetry・npm・Docker・GitHub Actions の依存更新を自動化（`.github/dependabot.yml`）。
- ルート / SpecStory / frontend の `.gitignore` を再編し、`.env.test` や `*.pem` を誤コミットから保護。
- README の Fork / 再利用ポリシーを更新し、運用ルールを明文化。

## 移行ガイド

1. アプリ起動時に `setup_exception_handlers` を適用していることを確認し、独自ハンドラーがある場合は整形済みレスポンス仕様に合わせて更新してください。
2. ルーター定義で `"/"` を付与しているエンドポイントがある場合、プレフィックスと重複しないよう調整してください。
3. structlog のコンテキストを独自に扱うサービスは、`RequestContextLogMiddleware` の適用順序とコンテキストキーの重複がないかを確認してください。

## テストと検証

- 単体テストおよび既存の E2E / 統合テストを実行し、例外ハンドリング変更によるレスポンス形式の差異がないことを確認します。
- slowapi を利用するルートでレート制限ヘッダーと監査ログが期待通り出力されることを検証します。
- Dependabot から Poetry / npm / Docker / GitHub Actions 用 Pull Request が作成されることを確認します。

## 関連コミット

- a61ffca: refactor: KOIKI_CORE エラーハンドラーのインポートの整理、バリデーションエラーの整形処理を追加
- 73ac915 / 63c0108: `.gitignore` ルール追加と `.env.*` サンプル整備
- b2404ec: Dependabot 設定を新規追加
- 8f1f22b / a66510c: frontend / SpecStory 向け `.gitignore` 整備
- a6f7cca: README 更新
- 226d628: API endpoint ベースパスのスラッシュなし統一対応
