# SAML環境変数設定クイックリファレンス

## 🎯 証明書取得戦略の選び方

### 推奨設定（本番環境）

```bash
# auto戦略: メタデータ優先 + 静的証明書フォールバック
SAML_CERT_FETCH_STRATEGY=auto
# Docker環境: コンテナサービス名を使用
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=3600
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"
```

**メリット:**
- ✅ IdPの証明書ローテーションに自動対応
- ✅ メタデータ取得失敗時も動作継続
- ✅ 署名検証エラー時の自動リトライ
- ✅ ゼロダウンタイム運用可能

---

### 開発環境（完全動的）

```bash
# metadata戦略: OIDC JWKS方式と同様
SAML_CERT_FETCH_STRATEGY=metadata
# Docker環境: コンテナサービス名を使用
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=3600
SAML_IDP_X509_CERT=""  # 不要
```

**メリット:**
- ✅ 証明書の手動管理不要
- ✅ IdP側の変更に即座に追従
- ✅ シンプルな設定

**デメリット:**
- ⚠️ メタデータ取得不可時は認証不可

---

### レガシー環境（静的証明書のみ）

```bash
# static戦略: 既存動作との完全互換
SAML_CERT_FETCH_STRATEGY=static
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"
SAML_IDP_METADATA_URL=""  # 不要
```

**メリット:**
- ✅ メタデータエンドポイント不要
- ✅ 既存実装との100%互換性

**デメリット:**
- ⚠️ 証明書ローテーション時に手動更新必要
- ⚠️ 証明書期限切れリスク

---

### 最大互換性（hybrid）

```bash
# hybrid戦略: 静的証明書で失敗時に動的取得
SAML_CERT_FETCH_STRATEGY=hybrid
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"
# Docker環境: コンテナサービス名を使用
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=3600
```

**メリット:**
- ✅ 静的証明書で通常動作
- ✅ 署名エラー時に自動的にメタデータから取得
- ✅ 移行期間に最適

---

## 📋 必須環境変数チェックリスト

### 全戦略共通

```bash
# Service Provider設定
SAML_SP_ENTITY_ID=http://localhost:8000/api/v1/auth/saml/metadata
SAML_SP_ACS_URL=http://localhost:8000/api/v1/auth/saml/acs
SAML_SP_SLS_URL=http://localhost:8000/api/v1/auth/saml/sls

# Identity Provider設定
SAML_IDP_ENTITY_ID=http://localhost:8090/realms/koiki-saml
SAML_IDP_SSO_URL=http://localhost:8090/realms/koiki-saml/protocol/saml
SAML_IDP_SLS_URL=http://localhost:8090/realms/koiki-saml/protocol/saml

# セキュリティ
SAML_RELAY_STATE_SIGNING_KEY=<強力なランダム文字列>

# リダイレクト設定
SAML_DEFAULT_REDIRECT_URI=http://localhost:3000/auth/saml/callback
SAML_ALLOWED_REDIRECT_URIS=http://localhost:3000/auth/saml/callback
```

### 戦略別の必須項目

| 戦略 | SAML_IDP_X509_CERT | SAML_IDP_METADATA_URL |
|------|-------------------|----------------------|
| auto | ✅ 推奨 | ✅ 必須 |
| metadata | ❌ 不要 | ✅ 必須 |
| static | ✅ 必須 | ❌ 不要 |
| hybrid | ✅ 必須 | ✅ 必須 |

---

## 🔧 証明書の取得方法

### 方法1: メタデータから自動取得（推奨）

```bash
# メタデータURLを設定するだけ
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor
```

証明書は自動的に抽出されます。

### 方法2: メタデータXMLから手動抽出

```bash
# 1. メタデータを取得（Docker環境）
curl http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor > metadata.xml

# 2. X509Certificate要素を抽出
grep -A 20 '<ds:X509Certificate>' metadata.xml

# 3. 証明書部分をコピー
# MIICozCCAYsCBgGZ... の部分を抽出

# 4. .envに設定
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
MIICozCCAYsCBgGZmtzESTANBgkqhkiG9w0BAQsFADAVMRMwEQYDVQQDDAprb2lr
...
-----END CERTIFICATE-----"

# 5. メタデータURLはコンテナサービス名を使用
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
```

### 方法3: Keycloak Admin Consoleから取得

```
1. http://localhost:8090 にアクセス
2. admin/admin でログイン
3. koiki-saml realm を選択
4. Realm Settings > Keys タブ
5. RS256 の "Certificate" ボタンをクリック
6. 表示された証明書をコピー
7. BEGIN/ENDヘッダーを追加して.envに設定
```

---

## ⚙️ 設定値の検証

### 1. メタデータURL接続確認

```bash
# Docker環境の場合: ホストから確認
curl -v http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor

# コンテナ内から確認（実際のアプリケーションの接続先）
docker exec -it osskk_fastapi_app curl -v http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
```

**期待される結果:**
- HTTP 200 OK
- XML形式のレスポンス
- `<EntityDescriptor>` タグが含まれる
- `<ds:X509Certificate>` 要素が含まれる

### 2. 証明書フォーマット確認

正しいフォーマット:
```
-----BEGIN CERTIFICATE-----
MIICozCCAYsCBgGZmtzESTANBgkqhkiG9w0BAQsFADAVMRMwEQYDVQQDDAprb2lr
aS1zYW1sMB4XDTI1MDkzMDEzNDEyM1oXDTM1MDkzMDEzNDMwM1owFTETMBEGA1UE
...（複数行）...
-----END CERTIFICATE-----
```

**チェックポイント:**
- ✅ `-----BEGIN CERTIFICATE-----` で始まる
- ✅ `-----END CERTIFICATE-----` で終わる
- ✅ Base64エンコードされた文字列
- ✅ 改行が保持されている

### 3. 環境変数読み込み確認

Pythonコンソールで確認:
```python
from app.core.saml_config import SAMLSettings

settings = SAMLSettings()
print(f"Strategy: {settings.SAML_CERT_FETCH_STRATEGY}")
print(f"Metadata URL: {settings.SAML_IDP_METADATA_URL}")
print(f"Has static cert: {bool(settings.SAML_IDP_X509_CERT)}")
print(f"Cache TTL: {settings.SAML_METADATA_CACHE_TTL_SECONDS}s")
```

---

## 🚨 よくあるエラーと対処法

### エラー1: "Failed to fetch metadata from IdP" (Docker環境)

**原因:**
- メタデータURLが間違っている
- **Docker環境でlocalhost:8090を使用している（最も一般的）**
- ネットワーク接続の問題
- IdPが起動していない

**対処法:**
```bash
# URLを確認
echo $SAML_IDP_METADATA_URL

# 接続テスト（ホストから）
curl http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor

# Docker環境の場合、サービス名を使用
# ❌ localhost:8090 (コンテナから接続不可)
# ✅ keycloak:8080 (コンテナ間通信)
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

# コンテナ内から接続確認
docker exec -it osskk_fastapi_app curl http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

# 設定変更後はコンテナ再起動
docker-compose restart app
```

**Docker環境とローカル開発の違い:**

| 環境 | メタデータURL | 説明 |
|------|--------------|------|
| Docker内（推奨） | `http://keycloak:8080/...` | コンテナ間通信 |
| ローカル開発 | `http://localhost:8090/...` | ホストから直接 |
| 本番環境 | `https://idp.example.com/...` | 公開URL |


### エラー2: "Signature validation failed"

**原因:**
- 証明書が古い（IdPで更新された）
- 証明書フォーマットが不正
- BEGIN/ENDヘッダーが欠落

**対処法:**
```bash
# auto/metadata戦略の場合: 自動的にリトライされる（ログを確認）
# static戦略の場合: 証明書を手動更新

# 証明書を再取得
curl http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor | \
  grep -A 20 '<ds:X509Certificate>'
```

### エラー3: "Certificate strategy 'xxx' not supported"

**原因:**
- `SAML_CERT_FETCH_STRATEGY` の値が不正

**対処法:**
```bash
# 有効な値: auto, metadata, static, hybrid
SAML_CERT_FETCH_STRATEGY=auto
```

---

## 🔄 証明書ローテーション時の挙動

### auto/metadata/hybrid戦略の場合

```
IdPで証明書更新
  ↓
次回認証時、署名検証エラー発生
  ↓
自動的にメタデータから新証明書取得
  ↓
キャッシュ更新
  ↓
再検証
  ↓
認証成功（ダウンタイムなし）
```

**ログ例:**
```
WARNING: Signature verification failed, attempting certificate refresh and retry
INFO: Certificate cache refreshed, retrying SAML verification
INFO: SAML verification succeeded after certificate refresh
```

### static戦略の場合

```
IdPで証明書更新
  ↓
次回認証時、署名検証エラー発生
  ↓
認証失敗（エラーレスポンス）
  ↓
【手動作業】.envファイルの証明書を更新
  ↓
アプリケーション再起動
  ↓
認証再開
```

---

## 📊 戦略別の比較表

| 項目 | auto | metadata | static | hybrid |
|------|------|----------|--------|--------|
| メタデータURL必要 | ✅ | ✅ | ❌ | ✅ |
| 静的証明書必要 | △ | ❌ | ✅ | ✅ |
| 自動ローテーション | ✅ | ✅ | ❌ | ✅ |
| フォールバック | ✅ | ❌ | - | ✅ |
| ダウンタイム | なし | なし | あり | なし |
| 設定の複雑さ | 低 | 低 | 低 | 中 |
| 推奨環境 | 本番 | 開発 | レガシー | 移行期 |

---

## 🎓 ベストプラクティス

### 本番環境

```bash
# auto戦略 + HTTPS + 適切なTTL
SAML_CERT_FETCH_STRATEGY=auto
SAML_IDP_METADATA_URL=https://idp.example.com/saml/metadata
SAML_METADATA_CACHE_TTL_SECONDS=3600
SAML_IDP_X509_CERT="..." # フォールバック用
SAML_SKIP_SSL_VERIFY=false
```

### 開発環境（Docker）

```bash
# metadata戦略 + コンテナサービス名 + 短いTTL
SAML_CERT_FETCH_STRATEGY=metadata
# Docker環境: コンテナサービス名を使用
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=300
SAML_SKIP_SSL_VERIFY=true  # 開発のみ
SAML_DEBUG_MODE=true
```

### 開発環境（ローカル）

```bash
# metadata戦略 + localhost
SAML_CERT_FETCH_STRATEGY=metadata
# ローカル開発: localhost使用
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=300
SAML_SKIP_SSL_VERIFY=true  # 開発のみ
SAML_DEBUG_MODE=true
```

### ステージング環境

```bash
# hybrid戦略 + 本番同等設定
SAML_CERT_FETCH_STRATEGY=hybrid
SAML_IDP_METADATA_URL=https://staging-idp.example.com/saml/metadata
SAML_METADATA_CACHE_TTL_SECONDS=3600
SAML_IDP_X509_CERT="..."
SAML_SKIP_SSL_VERIFY=false
```

---

## 参考ドキュメント

- [saml-integration-complete.md](./saml-integration-complete.md) - 統合完了ガイド
- [saml-certificate-strategies.md](./saml-certificate-strategies.md) - 証明書戦略詳細
- [saml-dynamic-metadata.md](./saml-dynamic-metadata.md) - 動的メタデータ取得
