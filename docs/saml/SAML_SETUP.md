# SAML認証設定ガイド

このドキュメントでは、KOIKI-FWでSAML認証を設定する方法を説明します。

## 概要

KOIKI-FWは以下のSAML認証機能を提供します：

- **SAML 2.0 Service Provider (SP)** として動作
- **Keycloak IdP** との統合
- **自動ユーザー作成・連携**
- **属性マッピング設定**
- **OIDCと同じAPIパターン**

## 前提条件

1. **Python依存関係**:
   ```bash
   poetry install  # python3-saml, xmlsec が含まれます
   ```

2. **Keycloak サーバー**:
   ```bash
   # Docker Composeで起動
   docker-compose up keycloak
   ```

## 設定手順

### 1. Docker Keycloak起動

```bash
# Keycloak + 両方のrealm（OIDC, SAML）を起動
 docker-compose up keycloak

 # ログで確認: realm-koiki.json と realm-saml.json が自動インポート
 docker logs osskk_keycloak

# Keycloak devモードのH2データベースは `keycloak_data` ボリュームに永続化されます。
# 設定を初期化したい場合は `docker-compose down -v keycloak` ではなく、
# `docker volume rm koiki-pyfw_keycloak_data` を実行してから再起動してください。
```

### 2. Keycloak SAML Realm設定

1. **Admin Console アクセス**:
   ```bash
   # Keycloak Admin Console にアクセス（Docker環境）
   http://localhost:8090

   # ログイン: admin / admin
   # koiki-saml realm が自動的にインポート済み
   ```

2. **証明書の取得**:
   ```bash
   # Keycloak Admin Console > koiki-saml realm > Realm Settings > Keys
   # RSA256の "Certificate" ボタンをクリックして証明書をコピー
   ```

### 3. アプリケーション設定

1. **環境変数設定**:
   ```bash
   cp .env.saml.example .env
   # .envファイルを編集して実際の値を設定
   ```

2. **Docker環境用設定項目**:
   ```bash
   # SP識別情報
   SAML_SP_ENTITY_ID=http://localhost:8000/api/v1/auth/saml/metadata
   SAML_SP_ACS_URL=http://localhost:8000/api/v1/auth/saml/acs

   # IdP識別情報（ブラウザアクセス用: localhost:8090）
   # ENTITY_ID, SSO_URL, SLS_URLはブラウザからもアクセスするため
   SAML_IDP_ENTITY_ID=http://localhost:8090/realms/koiki-saml
   SAML_IDP_SSO_URL=http://localhost:8090/realms/koiki-saml/protocol/saml

   # 証明書取得戦略（推奨: auto）
   SAML_CERT_FETCH_STRATEGY=auto

   # メタデータURL（重要: Docker環境ではコンテナサービス名を使用）
   # コンテナ間通信用: keycloak:8080
   # ホスト確認用: localhost:8090
   SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

   # IdP証明書（フォールバック用、auto戦略では省略可）
   SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"

   # RelayState署名キー（本番環境では必ず変更）
   SAML_RELAY_STATE_SIGNING_KEY=change_me_saml_relay_state_secret_in_production

   # ブラウザ戻り先と許可URI（必ずフロントエンドのホワイトリストを設定）
   SAML_DEFAULT_REDIRECT_URI=http://localhost:3000/auth/saml/callback
   SAML_ALLOWED_REDIRECT_URIS=http://localhost:3000/auth/saml/callback
   SAML_LOGIN_TICKET_TTL_SECONDS=120
   ```

### 3. アプリケーション起動

```bash
# 依存関係インストール
poetry install

# アプリケーション起動
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API エンドポイント

### SAML認証フロー

1. **認証開始**:
   ```http
   GET /auth/saml/authorization?redirect_uri=https://frontend.local/auth/saml/callback

   Response:
   {
     "sso_url": "http://localhost:8080/realms/koiki-saml/protocol/saml",
     "saml_request": "PHNhbWxwOkF1dGhuUmVxdWVzdC...",
     "relay_state": "eyJub25jZSI6Ii4uLiIsInJlcSI6Il9yZXEiLCJleHAiOjE3MzU2MDM4MDB9.wJ7...",
     "expires_at": "2024-11-01T12:10:00Z",
     "sso_binding": "HTTP-Redirect",
     "redirect_url": "http://localhost:8080/realms/koiki-saml/protocol/saml?SAMLRequest=...&RelayState=eyJub25j..."
   }
   ```

   フロントエンドは `redirect_url` をブラウザ遷移させるだけで、`RelayState`を自動的に引き継げます。

2. **IdPログイン + ACS処理**:

   IdPでの認証後、ユーザーのブラウザは `POST /api/v1/auth/saml/acs` に以下のフォームデータを送信します:

   ```http
   POST /api/v1/auth/saml/acs
   Content-Type: application/x-www-form-urlencoded

   SAMLResponse=...&RelayState=eyJub25...
   ```

   サーバー側ではSAML ResponseとRelayStateを検証し、ユーザーをローカルに連携した上で、
   `redirect_uri` にログインチケットを付与して303リダイレクトします。

   例: `https://frontend.local/auth/saml/callback?saml_ticket=ZXlKaGJHY2lPaUpTVXpJMU5pSjkuLi4`

3. **ログインチケット交換**:

   フロントエンドはリダイレクト先で `saml_ticket` を取得し、以下のAPIで内部トークンに交換します。
   チケットの有効期限は `SAML_LOGIN_TICKET_TTL_SECONDS`（既定120秒）です。

   ```http
   POST /auth/saml/login

   Request:
   {
     "login_ticket": "ZXlKaGJHY2lPaUpTVXpJMU5pSjkuLi4"
   }

   Response:
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer",
     "expires_in": 3600
   }
   ```

### 補助エンドポイント

- **ユーザー情報取得**: `GET /auth/saml/user-info`
- **ヘルスチェック**: `GET /auth/saml/health`

## テストユーザー

Realm-saml.jsonには以下のテストユーザーが含まれています：

| ユーザー名 | パスワード | メール | 部署 |
|-----------|-----------|--------|------|
| saml-user | Passw0rd! | saml-user@example.com | Engineering |
| saml-admin | AdminPass123! | saml-admin@example.com | Administration |
| saml-test | TestPass123! | saml-test@koiki.local | Engineering |

## 属性マッピング

デフォルトの属性マッピング:

```json
{
  "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
  "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
  "given_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
  "family_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
}
```

カスタム属性も設定可能:
- `department`: 部署情報
- `employee_id`: 社員ID

## セキュリティ設定

### 署名検証

```bash
# SAML Response/Assertion署名検証（推奨）
SAML_SIGN_RESPONSES=true
SAML_SIGN_ASSERTIONS=true

# SAML Request署名（オプション）
SAML_SIGN_REQUESTS=false
```

### ドメイン制限

```bash
# 許可ドメインの制限
SAML_ALLOWED_DOMAINS="example.com,koiki.local"
```

## トラブルシューティング

### よくある問題

1. **メタデータ接続エラー (Docker環境)**:
   ```
   エラー: Failed to fetch metadata from IdP: All connection attempts failed
   原因: localhost:8090を使用している（コンテナから接続不可）
   解決: SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
   確認: docker exec osskk_fastapi_app curl http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
   ```

2. **証明書エラー（署名検証失敗）**:
   ```
   エラー: Signature validation failed. SAML Response rejected
   
   原因1: 静的証明書が古い（IdPで証明書更新された）
   解決: メタデータから最新証明書を取得
         curl http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor | grep -A 20 X509Certificate
   
   原因2: メタデータURLが間違っている
   解決: コンテナ再起動後も同じエラーの場合、.envファイルを確認
         docker-compose down && docker-compose up -d
   
   原因3: 証明書フォーマットが不正
   解決: BEGIN CERTIFICATE/END CERTIFICATE行を含む完全な証明書を設定
   ```

3. **AttributeError**:
   ```
   エラー: Missing email attribute
   解決: Keycloak の属性マッピング設定を確認
   ```

4. **RelayState エラー**:
   ```
   エラー: RelayState token expired
   解決: SAML_RELAY_STATE_TTL_SECONDS の値を調整
   ```

### デバッグモード

```bash
# デバッグログを有効化
SAML_DEBUG_MODE=true

# SSL検証をスキップ（開発環境のみ）
SAML_SKIP_SSL_VERIFY=true
```

### ログ確認

```bash
# アプリケーションログ
tail -f logs/app.log | grep SAML

# Keycloakログ
docker logs keycloak | grep SAML
```

## フロントエンド統合

認証開始とログインチケット交換の最小実装例:

```javascript
// 認証開始（例: ログインボタン）
async function startSamlAuth() {
  const response = await fetch('/auth/saml/authorization?redirect_uri=' + encodeURIComponent('https://frontend.local/auth/saml/callback'));
  const data = await response.json();
  window.location.href = data.redirect_url; // RelayState入りのURL
}

// /auth/saml/callback ページ側処理
async function completeSamlLogin() {
  const params = new URLSearchParams(window.location.search);
  const loginTicket = params.get('saml_ticket');
  if (!loginTicket) {
    throw new Error('Missing saml_ticket');
  }

  const response = await fetch('/auth/saml/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login_ticket: loginTicket })
  });

  if (!response.ok) {
    throw new Error('SAML login failed');
  }

  const tokens = await response.json();
  // 任意の保存処理（Cookie / localStorage など）
  localStorage.setItem('access_token', tokens.access_token);
  window.location.href = '/dashboard';
}
```

## 本番環境設定

### 必須変更項目

1. **SSL設定**:
   ```bash
   SAML_SKIP_SSL_VERIFY=false
   ```

2. **署名キー**:
   ```bash
   # 強力なランダムキーを生成
   SAML_RELAY_STATE_SIGNING_KEY=$(openssl rand -base64 32)
   ```

3. **ドメイン設定**:
   ```bash
   SAML_SP_ENTITY_ID=https://yourdomain.com/api/v1/auth/saml/metadata
   SAML_SP_ACS_URL=https://yourdomain.com/api/v1/auth/saml/acs
   ```

### 証明書管理

本番環境では自己署名証明書ではなく、信頼できるCAから発行された証明書を使用してください。

## 参考資料

- [SAML 2.0 仕様](https://docs.oasis-open.org/security/saml/v2.0/)
- [Keycloak SAML ドキュメント](https://www.keycloak.org/docs/latest/server_admin/#saml)
- [python3-saml ライブラリ](https://github.com/onelogin/python3-saml)
