# Keycloak を利用した SSO 開発環境のセットアップ

## 概要
- Keycloak 公式イメージ (v25.0.2) を docker-compose に追加しました。
- `start-dev --import-realm` モードで起動し、リポジトリ同梱の `realm-koiki.json` を読み込むことで、最小限の Realm / Client / ユーザーが自動作成されます。
- 生成済みのクライアント (`koiki-backend`) とテストユーザー (`sso-user@example.com`) を用いて Authorization Code Flow + PKCE を通すことができます。

## 起動手順
1. `.env` に Keycloak 接続情報を設定するか、`.env.example` をコピーして値を調整します。
   ```bash
   cp .env.example .env
   ```
   - `SSO_STATE_SIGNING_KEY` は秘密値に置き換えてください。
   - `SSO_ALLOWED_REDIRECT_URIS` にフロントエンドのコールバックURLを列挙してください。

2. docker-compose を起動します。
   ```bash
   docker-compose up -d keycloak
   ```
   初回起動時に realm のインポートが走るため 30 秒程度かかります。健康チェックが `healthy` になったら FastAPI / Frontend コンテナも起動できます。

3. Keycloak 管理コンソール
   - URL: <http://localhost:8090/>
   - ユーザー名: `admin`
   - パスワード: `admin`
   - Realm: `koiki`

## インポートされる設定
### Client: `koiki-backend`
| 項目 | 値 |
|------|-----|
| Client Type | Confidential |
| Client Secret | `koiki-backend-secret` |
| Standard Flow | 有効 |
| PKCE | `S256` (属性 `pkce.code.challenge.method`) |
| Redirect URIs | `http://localhost:3000/*`, `http://host.docker.internal:3000/*`, `http://localhost:8000/sso/callback` |
| Default Scopes | `openid`, `email`, `profile`, `roles`, `web-origins` |

### テストユーザー
| 項目 | 値 |
|------|-----|
| Username | `sso-user` |
| Email | `sso-user@example.com` |
| Password | `Passw0rd!` |
| Email認証 | 済み (`emailVerified=true`) |

## FastAPI 側設定の確認
FastAPI コンテナ (サービス名 `app`) からは `http://keycloak:8080` で Keycloak に到達できます。以下の環境変数が正しくセットされているか確認してください。
```env
SSO_CLIENT_ID=koiki-backend
SSO_CLIENT_SECRET=koiki-backend-secret
SSO_ISSUER_URL=http://keycloak:8080/realms/koiki
SSO_AUTHORIZATION_ENDPOINT=http://keycloak:8080/realms/koiki/protocol/openid-connect/auth
SSO_TOKEN_ENDPOINT=http://keycloak:8080/realms/koiki/protocol/openid-connect/token
SSO_JWKS_URI=http://keycloak:8080/realms/koiki/protocol/openid-connect/certs
SSO_DEFAULT_SCOPES=openid email profile
SSO_DEFAULT_REDIRECT_URI=http://localhost:3000/sso/callback
SSO_ALLOWED_REDIRECT_URIS=http://localhost:3000/*,http://host.docker.internal:3000/*,http://localhost:8000/sso/callback
SSO_STATE_SIGNING_KEY=your_state_token_secret
```

## 動作確認の流れ
1. `GET /api/v1/sso/authorization` を叩いて `state` と `nonce` を取得します。
2. レスポンスの `authorization_base_url` に PKCE の `code_challenge` を付加し、ブラウザでアクセスします。
3. `sso-user@example.com / Passw0rd!` でログインすると、指定した `redirect_uri` に `code` と `state` が返ります。
4. `POST /api/v1/sso/login` に `authorization_code` / `code_verifier` / `state` / `nonce` / `redirect_uri` を送信し、内部アクセストークンが取得できることを確認します。

## 補足
- 別のクライアントやユーザーを作成する場合は、Keycloak 管理コンソール上で調整し、`realm-koiki.json` を再エクスポートしてリポジトリへ反映してください。
- 認可エンドポイントへのアクセスを HTTPS 化したい場合は、Keycloak の front-channel をリバースプロキシ経由で公開するか、Keycloak に TLS 証明書を設定してください。
- 本番向けには `start-dev` モードではなくデータベース永続化モードを利用し、管理者アカウント/クライアントシークレットを安全に管理してください。
