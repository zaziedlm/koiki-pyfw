# SAML証明書マネージャー統合完了ガイド

## 概要

SAMLServiceに柔軟な証明書取得戦略を統合し、動的メタデータ取得と静的証明書設定の両方をサポートする実装が完了しました。

## 実装内容

### 1. SAMLCertificateManagerの統合

#### SAMLService.__init__
```python
def __init__(self, saml_settings: SAMLSettings):
    self.saml_settings = saml_settings
    self.cert_manager = SAMLCertificateManager(self.saml_settings)  # 追加
```

証明書マネージャーをサービス初期化時にインスタンス化します。

#### SAMLService._build_saml_config (async化)
```python
async def _build_saml_config(self, acs_url: str) -> dict:
    """SAML設定を動的に構築（証明書を動的取得）"""
    
    # 証明書マネージャーから証明書を取得
    idp_x509cert = await self.cert_manager.get_signing_certificate()
```

- メソッドを`async`に変更
- 証明書取得を`cert_manager.get_signing_certificate()`経由で実行
- 戦略に応じて自動的にメタデータまたは静的証明書を使用

#### SAMLService.generate_authn_request (async化)
```python
async def generate_authn_request(
    self, acs_url: str = None, redirect_uri: str = None
) -> dict:
    """SAML認証リクエスト生成"""
    
    saml_config = await self._build_saml_config(acs_url_final)
```

- メソッドを`async`に変更
- `_build_saml_config`を`await`で呼び出し

#### SAMLService.verify_saml_response (署名エラー時の自動リトライ)
```python
async def verify_saml_response(
    self,
    *,
    request: Request,
    saml_response: str,
    relay_state_payload: Optional[dict] = None,
    retry_on_signature_error: bool = True,  # 新規パラメータ
) -> SAMLUserInfo:
```

**主要な変更:**

1. **署名エラーの検出**
```python
if errors:
    error_reason = auth.get_last_error_reason()
    # 署名関連のエラーかチェック
    if retry_on_signature_error and (
        "Signature validation failed" in str(error_reason)
        or "invalid_signature" in str(errors)
        or any("signature" in str(e).lower() for e in errors)
    ):
        signature_error_occurred = True
```

2. **証明書リフレッシュとリトライ**
```python
if signature_error_occurred:
    # 証明書キャッシュをリフレッシュ
    await self.cert_manager.refresh_on_verification_failure()
    
    # 新しい証明書で設定を再構築
    saml_config = await self._build_saml_config(...)
    auth = OneLogin_Saml2_Auth(request_data, onelogin_settings)
    
    # 再検証
    auth.process_response(request_id=request_id)
```

### 2. API Endpoint の更新

#### app/api/v1/endpoints/saml_auth.py

**saml_authorization_init endpoint**
```python
context = await saml_service.generate_authn_request(
    acs_url=acs_url,
    redirect_uri=redirect_uri,
)
```

`generate_authn_request`の呼び出しに`await`を追加。

## 証明書取得戦略

### 設定方法

`.env`または環境変数で設定:

```bash
# 証明書取得戦略 (auto|metadata|static|hybrid)
SAML_CERT_FETCH_STRATEGY=auto

# メタデータURL（metadata/auto/hybrid戦略で必要）
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor

# メタデータキャッシュTTL（秒）
SAML_METADATA_CACHE_TTL_SECONDS=3600

# 静的証明書（static/auto/hybrid戦略で使用）
SAML_IDP_X509_CERT="MIICmzCCAYMCBgGU..."
```

### 各戦略の動作

#### 1. auto（デフォルト・推奨）
```bash
SAML_CERT_FETCH_STRATEGY=auto
```

- **第1選択**: メタデータから動的取得
- **フォールバック**: 静的証明書
- **最も柔軟で本番推奨**

#### 2. metadata（完全動的）
```bash
SAML_CERT_FETCH_STRATEGY=metadata
```

- メタデータからのみ取得
- 静的証明書は使用しない
- OIDC JWKS方式と同様のアプローチ

#### 3. static（レガシー）
```bash
SAML_CERT_FETCH_STRATEGY=static
```

- 環境変数の静的証明書のみ使用
- メタデータは使用しない
- 既存動作との完全互換性

#### 4. hybrid（両方試行）
```bash
SAML_CERT_FETCH_STRATEGY=hybrid
```

- 静的証明書で失敗した場合、メタデータから取得してリトライ
- 最大限の互換性

## 自動リトライ機能

### 署名検証エラー時の挙動

1. **初回検証**: 現在の証明書で署名検証
2. **エラー検出**: 署名関連のエラーを自動検出
3. **証明書更新**: メタデータから最新の証明書を取得（キャッシュクリア）
4. **再検証**: 新しい証明書で再度検証

### メリット

- IdPの証明書ローテーション時にダウンタイムなし
- 手動での証明書更新が不要
- エンタープライズ環境でのゼロダウンタイム運用

### 無効化

リトライを無効にしたい場合:
```python
user_info = await saml_service.verify_saml_response(
    request=request,
    saml_response=saml_response,
    relay_state_payload=relay_payload,
    retry_on_signature_error=False,  # リトライ無効
)
```

## 動作確認

### 1. Keycloakメタデータの確認

```bash
curl http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor
```

X.509証明書が含まれていることを確認。

### 2. 証明書取得のテスト

```python
from app.services.saml_certificate_manager import SAMLCertificateManager
from app.core.saml_config import SAMLSettings

settings = SAMLSettings()
cert_manager = SAMLCertificateManager(settings)

# 証明書取得
cert = await cert_manager.get_signing_certificate()
print(f"Certificate obtained: {cert[:50]}...")

# ソース情報取得
info = cert_manager.get_certificate_source_info()
print(f"Source: {info['source']}")
print(f"Strategy: {info['strategy']}")
```

### 3. SAML認証フロー

1. **AuthnRequest生成**
   ```bash
   curl http://localhost:8000/api/v1/auth/saml/authorize
   ```

2. **IdPでログイン**
   ブラウザでKeycloakログイン画面へ遷移

3. **ACS処理**
   IdPからSAMLResponseを受け取り、署名検証を実行

### 4. ログ確認

署名エラー時のリトライログ:
```
WARNING: Signature verification failed, attempting certificate refresh and retry
INFO: Certificate cache refreshed, retrying SAML verification
INFO: SAML verification succeeded after certificate refresh
```

## トラブルシューティング

### メタデータが取得できない

**症状**: "Failed to fetch metadata from IdP"

**確認事項**:
```bash
# メタデータURLが正しいか
echo $SAML_IDP_METADATA_URL

# 接続確認
curl -v $SAML_IDP_METADATA_URL

# ネットワーク/Firewall確認
# Dockerコンテナの場合、localhost ではなく service名 を使用
SAML_IDP_METADATA_URL=http://keycloak:8090/realms/koiki-saml/protocol/saml/descriptor
```

### 署名検証に失敗する

**症状**: "SAML validation failed: Signature validation failed"

**確認事項**:
1. 証明書の形式が正しいか（BEGIN/END行含む）
2. 証明書が最新か（IdPで更新されていないか）
3. メタデータURLが正しいか

**デバッグ**:
```python
# 証明書ソースを確認
info = cert_manager.get_certificate_source_info()
logger.info(f"Current cert source: {info}")

# 強制リフレッシュ
await cert_manager.refresh_on_verification_failure()
```

### 戦略の切り替えが機能しない

**確認事項**:
```bash
# 環境変数を確認
echo $SAML_CERT_FETCH_STRATEGY

# アプリケーション再起動
docker-compose restart backend
```

## セキュリティ考慮事項

### メタデータ取得のセキュリティ

1. **HTTPS推奨**: 本番環境では必ずHTTPS経由でメタデータ取得
   ```bash
   SAML_IDP_METADATA_URL=https://idp.example.com/saml/metadata
   ```

2. **証明書検証**: IdPのTLS証明書を適切に検証

3. **キャッシュTTL**: 適切な期間を設定（デフォルト1時間）
   ```bash
   SAML_METADATA_CACHE_TTL_SECONDS=3600
   ```

### 証明書ローテーション

- `auto`または`hybrid`戦略を使用することで、証明書更新時の自動対応が可能
- 定期的なメタデータ更新により、IdPの証明書変更に自動追従

## 関連ドキュメント

- [saml-dynamic-metadata.md](./saml-dynamic-metadata.md) - 動的メタデータ取得の詳細
- [saml-certificate-strategies.md](./saml-certificate-strategies.md) - 証明書戦略の詳細ガイド
- [authentication-api-guide.md](./authentication-api-guide.md) - SAML認証API仕様

## まとめ

SAMLServiceに以下の機能が追加されました:

✅ 動的メタデータからの証明書取得  
✅ 4つの証明書取得戦略（auto/metadata/static/hybrid）  
✅ 署名検証エラー時の自動リトライ  
✅ 既存実装との後方互換性  
✅ エンタープライズ対応のゼロダウンタイム運用  

この実装により、OIDC同様の柔軟性と保守性を実現しつつ、SAML特有の要件にも対応しています。
