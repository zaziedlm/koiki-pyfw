# KOIKI-FW v0.7 Frontend SPA Migration - antigravity 点検結果報告書

本ドキュメントは、AIアシスタント antigravity によるフロントエンド SPA 移行計画およびタスク指示書の詳細点検（レビュー）結果を記録したものです。

---

## 1. 全体評価

現在のNext.js BFF（Backend-for-Frontend）構成を廃止し、フロントエンドをシンプルな Vite + React + TypeScript の SPA に置き換え、セキュリティ境界（Cookie、CSRF、SSO/SAML）を FastAPI バックエンドに集約するアプローチは、フレームワークへの結合度を下げ、アーキテクチャのポータビリティとセキュリティ強度を高める上で非常に妥当かつ優れた計画です。

一方で、実際のコード実装フェーズにおいて、セキュリティ上の脆弱性が残るリスクや、実装時のはまりどころになり得る以下の考慮事項を特定しました。これらを事前に設計およびタスクへ反映することを推奨します。

---

## 2. 詳細指摘事項と推奨される改善策

### 指摘 1: 【セキュリティ】FastAPIログイン・リフレッシュ系のレスポンスモデルの設計変更
* **対象コード / ファイル**:
  * [auth_basic.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/libkoiki/src/libkoiki/api/v1/endpoints/auth_basic.py) (`/login` エンドポイント)
  * [auth_token.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/libkoiki/src/libkoiki/api/v1/endpoints/auth_token.py) (`/refresh` エンドポイント)
  * [sso_auth.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/sso_auth.py) (`/sso/login` エンドポイント)
  * [saml_auth.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/saml_auth.py) (`/saml/login` エンドポイント)
* **現状と課題**:
  * 現在の各ログイン・リフレッシュエンドポイントは、`response_model=TokenWithRefresh` となっており、アクセストークンおよびリフレッシュトークンをJSONのレスポンスボディとしてブラウザに返却する設計になっています。
  * このままだと、バックエンドがCookie（HttpOnly）を設定したとしても、JSONレスポンスのボディからもトークン文字列がブラウザのJavaScriptに渡ってしまいます。結果として、フロントエンドの実装次第でそれらをローカルストレージ等にキャッシュして利用する余地が残ってしまい、XSSによるトークン漏洩リスクを完全に排除できなくなります。
* **改善策**:
  * 各エンドポイントの `response_model` を `TokenWithRefresh` からトークンを含まない別のレスポンススキーマ（例：`AuthResponse` やユーザー情報だけを返すスキーマ）に変更することを推奨します。
  * バックエンドはトークンを `Set-Cookie` ヘッダーのみに設定し、レスポンスボディからは完全に除外する必要があります。

### 指摘 2: 【セキュリティ】既存認証Dependency（`get_user_from_token`）のCookie対応
* **対象コード / ファイル**:
  * [security.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/libkoiki/src/libkoiki/core/security.py) (関数 `get_user_from_token`)
* **現状と課題**:
  * 現状の `get_user_from_token` は `oauth2_scheme = OAuth2PasswordBearer(...)` を使用しており、これは HTTP リクエストの `Authorization: Bearer <token>` ヘッダーからアクセストークンを抽出します。
  * SPA移行に伴い、ブラウザから自動送信されるCookie（`koiki_access_token`）で認証を行うようになると、ヘッダーに Bearer トークンを設定しなくなります。
  * タスク指示書（`task-1-1.md`など）では Cookie primitives の実装は指示されていますが、「既存の認証Dependency自体をCookie対応（またはヘッダーとCookieの両方をフォールバックでサポートする設計）にする」という変更タスクが明文化されていません。
* **改善策**:
  * `get_user_from_token` またはその上層のDependencyで、`Authorization` ヘッダーがない場合に `request.cookies.get("koiki_access_token")` からトークンを抽出するフォールバックロジックを実装することをタスクに明記することを推奨します。これにより、既存のテストコードや外部クライアント向けのBearer認証との互換性を保ちつつ、SPAからのCookie認証を処理できます。

### 指摘 3: 【セキュリティ・設計】SSO / SAML コールバック直後のリクエストに対するCSRF検証除外
* **対象コード / ファイル**:
  * [sso_auth.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/sso_auth.py) (`/sso/login`)
  * [saml_auth.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/koiki_ref_app/src/koiki_ref_app/api/v1/endpoints/saml_auth.py) (`/saml/login`)
* **現状と課題**:
  * SSOやSAMLのフローでは、外部IdP（Keycloak等）からACSを経由し、SPAのコールバックページ（`/sso/callback` や `/auth/saml/callback`）へリダイレクトされます。その直後に、SPAからバックエンドの `/saml/login` または `/sso/login` へ `POST` リクエスト（チケットやコードの交換）を送信します。
  * SPAから `POST` を投げるため、通常はCSRF検証（`x-csrf-token` ヘッダーとCookieの一致）が要求されますが、ユーザーがブラウザで初めてこのフローを行う場合（あるいはCookieがクリアされている場合）、SPA側にまだCSRFトークンCookieが存在しない、またはヘッダーにセットするためのトークンが手元にない状態があり得ます。
* **改善策**:
  * `/saml/login` および `/sso/login` は、ワンタイムのログインチケットやAuthorization Code（1回限り有効）を使用するエンドポイントであるため、CSRF攻撃が成立する可能性が極めて低いです。
  * したがって、これら認証のブートストラップ的な `POST` エンドポイントに関しては、**CSRF検証の対象外（除外）**にするように設計すべきです。この点を設計タスク（`task-0-2.md` や `task-1-3.md`）に考慮事項として明記することを推奨します。

### 指摘 4: 【設計・実装】トークンリフレッシュ（`/refresh`）のインプット・アウトプット設計の変更
* **対象コード / ファイル**:
  * [auth_token.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/libkoiki/src/libkoiki/api/v1/endpoints/auth_token.py) (`/refresh` エンドポイント)
  * [refresh_token.py](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/components/libkoiki/src/libkoiki/schemas/refresh_token.py) (スキーマ `RefreshTokenRequest`)
* **現状と課題**:
  * 現在の `/refresh` エンドポイントは、JSONボディで `refresh_token` を受け取る `RefreshTokenRequest` を使っています。
  * 移行後は、リフレッシュトークンが `HttpOnly` Cookie（`koiki_refresh_token`）に入っているため、フロントエンドのJavaScriptからは直接読み取れません。したがって、リクエストボディは空（不要）になり、Cookieの `koiki_refresh_token` を読み取る形に変わります。
* **改善策**:
  * `task-1-2.md`（password auth Cookie endpoints）に、`/refresh` エンドポイントのシグネチャ変更（リクエストボディの廃止とCookieからのトークン抽出）を明記し、不要となる `RefreshTokenRequest` スキーマの整理（または削除）も合わせて指示することを推奨します。

### 指摘 5: 【インフラ・デプロイ】Vite SPA移行に伴う静的配信サーバーでの404フォールバック（Redirection）設定
* **対象コード / ファイル**:
  * `frontend/Dockerfile` または Nginx等Webサーバー設定
* **現状と課題**:
  * Next.jsではサーバーサイドでルーティング（App Router）をハンドリングしていましたが、Vite SPAへ移行すると、ブラウザ側でのクライアントサイドルーティング（React Router）になります。
  * この状態で、SPAのURL（例：`/dashboard`）にブラウザで直接アクセスしたり、ページをリロードしたりすると、配信サーバーが物理的なファイルを探しに行き、404エラーになってしまいます。
* **改善策**:
  * Dockerや本番環境での配信方法を決定する `task-3-2.md`（Docker / environment migration）に、SPAのルーティングを正常に機能させるための**「404フォールバック設定（すべてのルートへのアクセスを `/index.html` に書き換える、またはフォールバックする設定）」**の追加をタスクとして明記することを推奨します。

### 指摘 6: 【テスト】結合テスト（Integration Test）におけるCookie/CSRFシミュレーションの補助
* **対象コード / ファイル**:
  * [task-1-4.md](file:///c:/Users/kataoka/Desktop/KOIKI-v07/koiki-v07/docs/dev/v0.7-frontend-spa-migration/task-1-4.md)
* **現状と課題**:
  * `task-1-4.md` では、`backend auth integration tests` を追加することが定義されています。
  * FastAPIの `TestClient` や `AsyncClient` を使用してCookie認証やCSRFのテストを書く際、テストクライアント側でCookieの自動保持（Cookie Jarのシミュレーション）や、`x-csrf-token` ヘッダーの設定を正しくシミュレートする必要があります。これらは単純なBearerヘッダーのテストに比べてボイラープレートコードが多くなりがちです。
* **改善策**:
  * テストタスク（`task-1-4.md`）に、テストを効率的かつ正確に行うための「Cookie保持およびCSRFヘッダー自動付与を行うテストクライアント用ヘルパー（テスト用ユーティリティ）」の設計・実装をサブタスクとして含めることを推奨します。
