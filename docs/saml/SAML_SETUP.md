# SAML認証設定ガイド

このドキュメントでは、KOIKI-FWでSAML認証を設定する方法を説明します。

> **最終更新**: Phase 1〜4 セキュリティ改修反映済み

## 概要

KOIKI-FWは以下のSAML認証機能を提供します：

- **SAML 2.0 Service Provider (SP)** として動作
- **Keycloak / HENNGE ONE 等の IdP** との統合
- **自動ユーザー作成・SSO連携**
- **柔軟な属性マッピング設定**
- **HKDF 鍵派生**による RelayState / ログインチケットの署名分離
- **DB状態管理**によるチケットリプレイ防御（`SELECT FOR UPDATE`）
- **証明書の動的取得**と署名検証失敗時の自動リトライ
- **定期フロークリーンアップ**タスク

## 前提条件

1. **Python依存関係**:
   ```bash
   poetry install  # python3-saml, xmlsec が含まれます
   ```

2. **PostgreSQL**: SAML認証フローの状態管理に `saml_auth_flow` テーブルを使用

3. **Keycloak サーバー**:
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

# Keycloak devモードのH2データベースは keycloak_data ボリュームに永続化されます。
# 設定を初期化したい場合は docker volume rm koiki-pyfw_keycloak_data を実行してから再起動してください。
```

### 2. Keycloak SAML Realm設定

1. **Admin Console アクセス**:
   ```
   URL: http://localhost:8090
   ログイン: admin / admin
   koiki-saml realm が自動的にインポート済み
   ```

2. **証明書の取得**（`auto` 戦略の場合は不要）:
   ```
   Keycloak Admin Console > koiki-saml realm > Realm Settings > Keys
   RSA256の "Certificate" ボタンをクリックして証明書をコピー
   ```

### 3. アプリケーション設定

1. **環境変数設定**:
   ```bash
   cp .env.saml.example .env
   # .envファイルを編集して実際の値を設定
   ```

2. **Docker環境用の主要設定項目**:
   ```bash
   # --- SP識別情報 ---
   SAML_SP_ENTITY_ID=http://localhost:8000/api/v1/auth/saml/metadata
   SAML_SP_ACS_URL=http://localhost:8000/api/v1/auth/saml/acs

   # --- IdP識別情報（ブラウザアクセス用: localhost:8090）---
   SAML_IDP_ENTITY_ID=http://localhost:8090/realms/koiki-saml
   SAML_IDP_SSO_URL=http://localhost:8090/realms/koiki-saml/protocol/saml

   # --- 証明書取得戦略（推奨: auto）---
   SAML_CERT_FETCH_STRATEGY=auto

   # メタデータURL（重要: Docker環境ではコンテナサービス名を使用）
   SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

   # IdP証明書（auto戦略のフォールバック用、省略可）
   SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"

   # --- 署名キー（必須・本番環境では必ず変更）---
   # このキーから HKDF で RelayState用・ログインチケット用の2つの鍵を派生します
   SAML_RELAY_STATE_SIGNING_KEY=change_me_saml_relay_state_secret_in_production

   # --- リダイレクト設定 ---
   SAML_DEFAULT_REDIRECT_URI=http://localhost:3000/auth/saml/callback
   SAML_ALLOWED_REDIRECT_URIS=http://localhost:3000/auth/saml/callback
   SAML_LOGIN_TICKET_TTL_SECONDS=120
   ```

   > 全環境変数の詳細は `saml-env-config-guide.md` を参照してください。

### 4. アプリケーション起動

```bash
# 依存関係インストール
poetry install

# アプリケーション起動
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker統合環境の場合
.\start-docker.ps1 unified-prod
```

### 5. データベースマイグレーション

```bash
# saml_auth_flow テーブルの作成
alembic upgrade head
```

## 認証フロー詳細

### シーケンス概要

```
ブラウザ       フロントエンド(Next.js)    バックエンド(FastAPI)      DB           IdP(Keycloak)
  │                │                        │                     │              │
  │─ログインクリック→│                        │                     │              │
  │                │─GET /api/saml/auth──────→│                     │              │
  │                │                        │─AuthnRequest生成─────│              │
  │                │                        │─DBフロー作成(authn_requested)─→│    │
  │                │←─ redirect_url ────────│                     │              │
  │                │─expires_at事前チェック──│                     │              │
  │←─302 IdPへリダイレクト─│                │                     │              │
  │─────────────────────────────────────────────────────────────→│              │
  │                │                        │                     │    IdPログイン│
  │←─────────────── POST SAMLResponse + RelayState ──────────────│              │
  │─POST /acs─────────────────────────────→│                     │              │
  │                │                        │─RelayState署名検証──│              │
  │                │                        │─SAMLResponse検証────│              │
  │                │                        │─ユーザー認証/作成───│              │
  │                │                        │─チケット発行────────│              │
  │                │                        │─DB更新(acs_verified)→│             │
  │←─303 callback?saml_ticket=xxx&relay_state=yyy──│             │              │
  │─────────────→│                        │                     │              │
  │                │─POST /api/saml/login──→│                     │              │
  │                │                        │─チケット署名検証────│              │
  │                │                        │─RelayState nonce照合│              │
  │                │                        │─DB排他ロック(SELECT FOR UPDATE)─→│ │
  │                │                        │─DB更新(ticket_consumed)──→│       │
  │                │                        │─JWTトークンペア発行──│              │
  │                │←─ access_token, refresh_token ─│             │              │
  │←── Cookie設定 + /dashboard遷移 ──│      │                     │              │
```

### 状態遷移（DB `saml_auth_flow` テーブル）

```
authn_requested ──ACS検証成功──→ acs_verified ──チケット交換成功──→ ticket_consumed
       │                              │
       └──期限切れ──→ expired ←───期限切れ──┘
```

## API エンドポイント

### SAML認証フロー

1. **認証開始** `GET /api/v1/auth/saml/authorization`

   ```http
   GET /api/v1/auth/saml/authorization?redirect_uri=http://localhost:3000/auth/saml/callback

   Response: 200 OK
   {
     "sso_url": "http://localhost:8090/realms/koiki-saml/protocol/saml",
     "saml_request": "PHNhbWxwOkF1dGhuUmVxdWVzdC...",
     "relay_state": "eyJub25jZSI6Ii4uLiJ9.HMAC署名...",
     "expires_at": "2026-02-28T12:10:00Z",
     "sso_binding": "HTTP-Redirect",
     "redirect_url": "http://localhost:8090/realms/koiki-saml/protocol/saml?SAMLRequest=...&RelayState=..."
   }
   ```

   - Rate Limit: 30/分
   - `@transactional` でDBフローレコード自動作成（status: `authn_requested`）
   - フロントエンドは `redirect_url` にブラウザ遷移するだけ

2. **ACS（Assertion Consumer Service）** `POST /api/v1/auth/saml/acs`

   IdPでの認証後、ブラウザがフォームPOSTで送信：

   ```http
   POST /api/v1/auth/saml/acs
   Content-Type: application/x-www-form-urlencoded

   SAMLResponse=...&RelayState=eyJub25j...
   ```

   - Rate Limit: 60/分
   - `@transactional` でDB更新自動コミット
   - サーバー側処理：RelayState HMAC署名検証 → SAML Response署名検証 → 属性抽出 → ユーザー認証/作成 → ログインチケット発行 → DB更新（status: `acs_verified`）
   - 署名検証失敗時は証明書を自動リフレッシュしてリトライ
   - 成功時: `303 Redirect` → `http://localhost:3000/auth/saml/callback?saml_ticket=xxx&relay_state=yyy`

3. **ログインチケット交換** `POST /api/v1/auth/saml/login`

   ```http
   POST /api/v1/auth/saml/login
   Content-Type: application/json

   {
     "login_ticket": "eyJ0aWQiOiIuLi4ifQ.HMAC署名...",
     "relay_state": "eyJub25jZSI6Ii4uLiJ9.HMAC署名..."
   }

   Response: 200 OK
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer",
     "expires_in": 3600
   }
   ```

   - Rate Limit: 10/分
   - `@transactional` + `@handle_auth_errors`
   - サーバー側処理：チケット署名検証 → RelayState署名再検証 → **nonce照合**（チケット内とRelayState内が一致すること） → **DB排他ロック**（`SELECT FOR UPDATE`）でチケット消費 → DB更新（status: `ticket_consumed`） → JWTトークンペア発行

### 補助エンドポイント

| エンドポイント | メソッド | Rate Limit | 説明 |
|---|---|---|---|
| `/api/v1/auth/saml/metadata` | GET | 10/分 | SP メタデータ XML |
| `/api/v1/auth/saml/user-info` | GET | 30/分 | SAML連携ユーザー情報（要認証） |
| `/api/v1/auth/saml/logout` | POST | 30/分 | SAML SLO開始（要認証） |
| `/api/v1/auth/saml/sls` | GET/POST | 60/分 | IdPからのSLO要求/応答受信 |
| `/api/v1/auth/saml/health` | GET | 60/分 | ヘルスチェック |

## テストユーザー

realm-saml.json には以下のテストユーザーが含まれています：

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

カスタム属性も設定可能（`SAML_ATTRIBUTE_MAPPING` 環境変数で JSON 指定）:
- `department`: 部署情報
- `employee_id`: 社員ID

## セキュリティ設計

### HKDF鍵派生（Phase 1）

1つの `SAML_RELAY_STATE_SIGNING_KEY`（マスターキー）から用途別の鍵を派生：

| 用途 | 派生パラメータ | 使用箇所 |
|---|---|---|
| RelayState署名 | `HMAC-SHA256(master, "relay_state")` | AuthnRequest生成時、ACS受信時 |
| ログインチケット署名 | `HMAC-SHA256(master, "login_ticket")` | チケット発行時、チケット交換時 |

鍵分離により、一方の署名が漏洩しても他方には影響しません。

### DB状態管理とリプレイ防御（Phase 2）

- `saml_auth_flow` テーブルで認証フロー全体のライフサイクルを管理
- チケット交換時に `SELECT FOR UPDATE` で行ロックを取得し、分散環境での二重消費を防止
- 期限切れフローは5分間隔のバックグラウンドタスクで自動クリーンアップ

### 証明書の動的取得と自動リトライ（Phase 3）

- 証明書取得戦略: `auto`（推奨）/ `metadata` / `static` / `hybrid`
- 署名検証失敗時に IdP メタデータから最新証明書を自動取得してリトライ
- 詳細は `saml-certificate-strategies.md` を参照

### 署名検証

```bash
# SAML Response / Assertion 署名検証（推奨: 両方有効）
SAML_SIGN_RESPONSES=true
SAML_SIGN_ASSERTIONS=true

# AuthnRequest 署名（IdP側の要件に応じて有効化）
SAML_SIGN_REQUESTS=false
```

### リダイレクトURI制限

```bash
# 許可されたリダイレクト先のみ受け付け（カンマ区切り）
SAML_ALLOWED_REDIRECT_URIS=http://localhost:3000/auth/saml/callback
# 未許可URIは SAML_DEFAULT_REDIRECT_URI にフォールバック
```

### ドメイン制限

```bash
# 許可ドメインの制限（カンマ区切り、空=制限なし）
SAML_ALLOWED_DOMAINS="example.com,koiki.local"
```

### フロントエンド側の防御（Phase 4）

- IdP リダイレクト前に `expires_at` の残り時間をチェック（閾値 30 秒未満ならリダイレクト中止）
- コールバックページで `expiresAt` の事後チェック（二重防御）

## トラブルシューティング

### よくある問題

1. **メタデータ接続エラー (Docker環境)**:
   ```
   エラー: Failed to fetch metadata from IdP: All connection attempts failed
   原因: SAML_IDP_METADATA_URL に localhost:8090 を指定（コンテナから接続不可）
   解決: SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
   確認: docker exec koiki_app_prod_unified curl http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
   ```

2. **証明書エラー（署名検証失敗）**:
   ```
   エラー: Signature validation failed. SAML Response rejected

   原因: 静的証明書が古い（IdPで証明書更新された）
   解決: auto 戦略であれば自動リトライされるため通常は自己回復する。
         static 戦略の場合はメタデータから最新証明書を手動取得:
         curl http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor | grep -A 20 X509Certificate
   ```

3. **チケット交換エラー（already used）**:
   ```
   エラー: Login ticket has already been used or expired
   原因: チケットの二重使用（ブラウザのリロード等）
   解決: 正常動作。ユーザーにはログイン画面へのリダイレクトが表示される
   ```

4. **RelayState エラー**:
   ```
   エラー: RelayState token expired
   解決: SAML_RELAY_STATE_TTL_SECONDS の値を調整（デフォルト: 600秒）
   ```

5. **属性マッピングエラー**:
   ```
   エラー: Missing email attribute
   解決: Keycloak の Client Scopes > 属性マッピング設定を確認
   ```

### デバッグ

```bash
# デバッグログを有効化
SAML_DEBUG_MODE=true

# SSL検証をスキップ（開発環境のみ）
SAML_SKIP_SSL_VERIFY=true
```

### ログ確認（Docker環境）

```bash
# バックエンドログ（SAML関連）
docker logs koiki_app_prod_unified --tail 100 2>&1 | grep -i saml

# クリーンアップタスクの動作確認
docker logs koiki_app_prod_unified --tail 50 2>&1 | grep -i cleanup

# Keycloakログ
docker logs osskk_keycloak_unified --tail 100 2>&1 | grep -i saml
```

## フロントエンド統合

KOIKI-FW のフロントエンド（Next.js）は BFF パターンで SAML 認証を統合しています。

### 主要ファイル

| ファイル | 役割 |
|---|---|
| `src/hooks/use-saml-login.ts` | SAML ログイン開始フック（`expires_at` 事前チェック含む） |
| `src/app/auth/saml/callback/page.tsx` | コールバックページ（チケット交換処理） |
| `src/app/api/saml/authorization/route.ts` | BFF: 認証開始プロキシ |
| `src/app/api/saml/login/route.ts` | BFF: チケット交換プロキシ（Cookie設定） |
| `src/lib/saml-storage.ts` | sessionStorage でのSAMLコンテキスト管理 |

### 最小実装例（参考）

```javascript
// 認証開始（ログインボタン）
async function startSamlAuth() {
  const res = await fetch('/api/saml/authorization?redirect_uri='
    + encodeURIComponent('http://localhost:3000/auth/saml/callback'));
  const data = await res.json();

  // expires_at の残り時間チェック（30秒未満ならエラー）
  if (data.expires_at) {
    const remaining = (new Date(data.expires_at).getTime() - Date.now()) / 1000;
    if (remaining < 30) throw new Error('Authorization state expires too soon');
  }

  window.location.href = data.redirect_url;
}

// コールバックページ処理
async function completeSamlLogin() {
  const params = new URLSearchParams(window.location.search);
  const ticket = params.get('saml_ticket');
  const relayState = params.get('relay_state');
  if (!ticket) throw new Error('Missing saml_ticket');

  const res = await fetch('/api/saml/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login_ticket: ticket, relay_state: relayState }),
  });

  if (!res.ok) throw new Error('SAML login failed');
  window.location.href = '/dashboard';
}
```

## 本番環境設定

### 必須変更項目

1. **SSL設定**:
   ```bash
   SAML_SKIP_SSL_VERIFY=false
   ```

2. **署名キー**（十分なエントロピーを確保）:
   ```bash
   SAML_RELAY_STATE_SIGNING_KEY=$(openssl rand -base64 32)
   ```

3. **ドメイン設定**:
   ```bash
   SAML_SP_ENTITY_ID=https://yourdomain.com/api/v1/auth/saml/metadata
   SAML_SP_ACS_URL=https://yourdomain.com/api/v1/auth/saml/acs
   ```

4. **リダイレクト URI のホワイトリスト**:
   ```bash
   SAML_DEFAULT_REDIRECT_URI=https://yourdomain.com/auth/saml/callback
   SAML_ALLOWED_REDIRECT_URIS=https://yourdomain.com/auth/saml/callback
   ```

5. **データベースマイグレーション**:
   ```bash
   alembic upgrade head  # saml_auth_flow テーブル作成
   ```

### 証明書管理

- 本番環境では `auto` 戦略を推奨（メタデータ優先 + 静的証明書フォールバック）
- 詳細は `saml-certificate-strategies.md` を参照

## 関連ドキュメント

| ドキュメント | 内容 |
|---|---|
| `saml-certificate-strategies.md` | 証明書取得戦略（auto/metadata/static/hybrid）の詳細 |
| `saml-env-config-guide.md` | 全SAML環境変数のクイックリファレンス |
| `saml-security-review.md` | セキュリティレビュー結果と対応状況 |
| `saml-dynamic-certificate-test.md` | 動的証明書取得のテスト手順 |
| `.env.saml.example` | 環境変数テンプレート |

## 参考資料

- [SAML 2.0 仕様](https://docs.oasis-open.org/security/saml/v2.0/)
- [Keycloak SAML ドキュメント](https://www.keycloak.org/docs/latest/server_admin/#saml)
- [python3-saml ライブラリ](https://github.com/onelogin/python3-saml)
