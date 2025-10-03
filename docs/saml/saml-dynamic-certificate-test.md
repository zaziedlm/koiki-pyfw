# SAML動的証明書取得テストガイド

## テスト目的

**auto戦略**での動的証明書取得機能が正しく動作することを確認します。

### テストシナリオ

静的証明書（`.env`の`SAML_IDP_X509_CERT`）をわざと古い/間違った状態にし、メタデータからの動的証明書取得で認証が成功することを検証します。

## 現在の設定状態

### 証明書の状態

| 項目 | 値 | 状態 |
|------|-----|------|
| **Keycloakの現在の証明書** | `MIICozCCAYsCBgGZoxqRzz...` | 2025-10-02生成（最新） |
| **`.env`の静的証明書** | `MIICozCCAYsCBgGZmtzEST...` | 2025-09-30生成（古い） |
| **証明書一致** | ❌ **不一致** | テスト用に意図的に不一致 |

### `.env`設定

```bash
# 証明書取得戦略
SAML_CERT_FETCH_STRATEGY=auto

# メタデータURL（コンテナサービス名）
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

# 静的証明書（わざと古いまま）
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
MIICozCCAYsCBgGZmtzESTANBgkqhkiG9w0BAQsFADAV...
-----END CERTIFICATE-----"
```

## 期待される動作フロー

### シナリオ1: メタデータ取得成功（正常系）

```
1. SAML認証開始
   ↓
2. 証明書取得試行（auto戦略）
   ├─ メタデータから取得を試行
   ├─ ✅ 成功: http://keycloak:8080/... から取得
   └─ 最新の証明書を取得
   ↓
3. SAML Response検証
   ├─ 最新の証明書で署名検証
   └─ ✅ 検証成功
   ↓
4. ✅ 認証成功
```

**期待されるログ:**
```
Fetching SAML IdP metadata {'url': 'http://keycloak:8080/...'}
Certificate loaded from metadata successfully
SAML Response verification successful
```

### シナリオ2: 署名エラー時の自動リトライ（異常系→復旧）

```
1. SAML認証開始
   ↓
2. 証明書取得試行（何らかの理由で静的証明書が使われた）
   ├─ メタデータ取得失敗（一時的）
   └─ 静的証明書（古い）を使用
   ↓
3. SAML Response検証
   ├─ 古い証明書で署名検証
   └─ ❌ 検証失敗（Signature validation failed）
   ↓
4. 署名エラー検出 → 自動リトライ
   ├─ 証明書キャッシュクリア
   ├─ メタデータから再取得
   └─ ✅ 最新の証明書を取得
   ↓
5. SAML Response再検証
   ├─ 最新の証明書で署名検証
   └─ ✅ 検証成功
   ↓
6. ✅ 認証成功（自動復旧）
```

**期待されるログ:**
```
Metadata fetch failed, falling back to static certificate
Certificate loaded from static configuration
Signature verification failed, attempting certificate refresh and retry
Verification failed, attempting to refresh certificate
Certificate cache refreshed, retrying SAML verification
Fetching SAML IdP metadata {'url': 'http://keycloak:8080/...'}
Certificate loaded from metadata successfully
SAML verification succeeded after certificate refresh
```

## テスト手順

### 1. 事前確認

```bash
# 設定確認
grep SAML_CERT_FETCH_STRATEGY .env
grep SAML_IDP_METADATA_URL .env

# メタデータ接続確認
docker exec osskk_fastapi_app curl -s http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor | head -10

# コンテナ起動確認
docker-compose ps
```

### 2. ログ監視開始

```bash
# ターミナル1: SAML関連ログを監視
docker-compose logs -f app | grep -E "SAML|metadata|Certificate|Signature"
```

### 3. SAML認証テスト

#### フロントエンドから（推奨）

1. ブラウザで `http://localhost:3000` にアクセス
2. "SAML Login" ボタンをクリック
3. Keycloakログインページが表示される
4. テストユーザーでログイン:
   - ユーザー名: `saml-user`
   - パスワード: `Passw0rd!`
5. 認証成功を確認

#### APIから直接テスト

```bash
# ターミナル2: 認証開始
curl -X GET "http://localhost:8000/api/v1/auth/saml/authorization?redirect_uri=http://localhost:3000/auth/saml/callback" | jq

# redirect_url をブラウザで開く
```

### 4. ログ確認ポイント

#### ✅ 成功パターン（メタデータから取得）

```
Fetching SAML IdP metadata {'url': 'http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor'}
Certificate loaded from metadata successfully
SAML Response verification successful
```

#### ✅ 成功パターン（リトライで復旧）

```
Signature verification failed, attempting certificate refresh and retry
Certificate cache refreshed, retrying SAML verification
Fetching SAML IdP metadata
Certificate loaded from metadata successfully
SAML verification succeeded after certificate refresh
```

#### ❌ 失敗パターン

```
Failed to fetch metadata from IdP: All connection attempts failed
Metadata fetch failed, falling back to static certificate
Signature validation failed. SAML Response rejected
SAML Response validation failed after retry
```

## 検証項目チェックリスト

### 証明書取得

- [ ] メタデータURLへの接続成功
- [ ] メタデータから証明書を抽出成功
- [ ] 証明書キャッシュが機能している

### 署名検証

- [ ] 正しい証明書で署名検証成功
- [ ] 署名エラー時の自動検出
- [ ] 証明書リフレッシュの実行

### 自動リトライ

- [ ] 署名エラー検出後のリトライ実行
- [ ] メタデータ再取得の実行
- [ ] 新しい証明書での再検証成功

### エンドツーエンド

- [ ] SAML認証フロー全体の成功
- [ ] ユーザー情報の正しい取得
- [ ] アクセストークンの発行成功

## トラブルシューティング

### メタデータ取得失敗

**ログ:**
```
Failed to fetch metadata from IdP: All connection attempts failed
```

**確認:**
```bash
# コンテナ内から接続確認
docker exec osskk_fastapi_app curl http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

# ネットワーク確認
docker-compose ps
docker network ls
```

### 署名検証が常に失敗

**ログ:**
```
Signature validation failed. SAML Response rejected
SAML Response validation failed after retry
```

**確認:**
```bash
# Keycloakの現在の証明書を取得
curl -s http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor | \
  grep -o '<ds:X509Certificate>[^<]*' | sed 's/<ds:X509Certificate>//'

# メタデータURLが正しいか確認
docker exec osskk_fastapi_app env | grep SAML_IDP_METADATA_URL
```

### 静的証明書にフォールバックし続ける

**ログ:**
```
Metadata fetch failed, falling back to static certificate
Cannot refresh static certificate, verification may continue to fail
```

**原因:**
- メタデータURLが間違っている
- ネットワーク接続の問題
- Keycloakが起動していない

**解決:**
```bash
# メタデータURLを確認
grep SAML_IDP_METADATA_URL .env

# 正しいURLに修正（Docker環境）
SAML_IDP_METADATA_URL=http://keycloak:8080/realms/koiki-saml/protocol/saml/descriptor

# コンテナ再起動
docker-compose restart app
```

## テスト結果の記録

### テスト実行日時
<!-- 記入してください -->

### テスト結果
<!-- ✅ 成功 / ❌ 失敗 / ⚠️ 部分的成功 -->

### 観測されたログ
```
<!-- ログを貼り付けてください -->
```

### 発見された問題
<!-- 問題があれば記入してください -->

### 備考
<!-- その他の気づきなど -->

## 次のステップ

### テスト成功後

1. **metadata戦略のテスト**:
   ```bash
   # 静的証明書を完全に無効化
   SAML_CERT_FETCH_STRATEGY=metadata
   SAML_IDP_X509_CERT=""
   ```

2. **証明書ローテーションのシミュレーション**:
   - Keycloakで新しい証明書を生成
   - 自動リトライが動作することを確認

3. **本番環境への展開準備**:
   - HTTPS URLへの変更
   - セキュリティ設定の見直し

### テスト失敗時

1. ログの詳細分析
2. ネットワーク設定の確認
3. 証明書フォーマットの検証
4. Keycloak設定の確認

## 参考資料

- [saml-certificate-strategies.md](./saml-certificate-strategies.md) - 証明書戦略の詳細
- [saml-integration-complete.md](./saml-integration-complete.md) - 統合完了ガイド
- [saml-env-config-guide.md](./saml-env-config-guide.md) - 環境変数設定ガイド
