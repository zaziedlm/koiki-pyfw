# SAMLにおける証明書管理の簡素化アプローチ

## 概要

OIDC認証では`.well-known/openid-configuration`とJWKSエンドポイントから動的に公開鍵を取得できますが、SAMLでも同様のアプローチが可能です。

## SAMLでの動的メタデータ取得

### 1. **従来の方式（手動設定）**

```bash
# .env
SAML_IDP_ENTITY_ID=http://localhost:8090/realms/koiki-saml
SAML_IDP_SSO_URL=http://localhost:8090/realms/koiki-saml/protocol/saml
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----\nMIIC...（長い証明書）\n-----END CERTIFICATE-----"
```

**問題点：**
- ❌ IdPから証明書を手動でコピー
- ❌ 証明書更新時に手動で再設定
- ❌ 設定ミスのリスク

### 2. **動的メタデータ取得方式（推奨）**

```bash
# .env - これだけでOK！
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=3600  # キャッシュ有効期限
```

**メリット：**
- ✅ IdPメタデータURLを指定するだけ
- ✅ 証明書が自動取得される
- ✅ 証明書ローテーションに自動対応
- ✅ 設定が簡潔でミスが少ない

## 実装方法

### ステップ1: SAMLサービスに統合

```python
# app/services/saml_service.py に追加

from app.services.saml_metadata_loader import SAMLMetadataLoader

class SAMLService:
    def __init__(self, ...):
        # 既存のコード...
        
        # メタデータローダー初期化
        if self.saml_settings.SAML_IDP_METADATA_URL:
            self.metadata_loader = SAMLMetadataLoader(
                metadata_url=self.saml_settings.SAML_IDP_METADATA_URL,
                cache_ttl_seconds=self.saml_settings.SAML_METADATA_CACHE_TTL_SECONDS,
                ssl_verify=not self.saml_settings.SAML_SKIP_SSL_VERIFY,
            )
        else:
            self.metadata_loader = None
    
    async def _get_idp_certificate(self) -> str:
        """IdP証明書を取得（動的または静的）"""
        if self.metadata_loader:
            # 動的メタデータから取得
            certificates = await self.metadata_loader.get_signing_certificates()
            return certificates.get("signing", next(iter(certificates.values())))
        else:
            # 従来の静的設定から取得
            return self.saml_settings.SAML_IDP_X509_CERT
    
    def _build_saml_config(self, acs_url: str) -> Dict[str, Any]:
        """SAML設定を構築"""
        # 既存のコードを修正して動的証明書に対応
        idp_cert = asyncio.run(self._get_idp_certificate()) if self.metadata_loader else self.saml_settings.SAML_IDP_X509_CERT
        
        return {
            "sp": {...},
            "idp": {
                "entityId": self.saml_settings.SAML_IDP_ENTITY_ID,
                "singleSignOnService": {
                    "url": self.saml_settings.SAML_IDP_SSO_URL,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": idp_cert,  # 動的に取得した証明書
            },
        }
```

### ステップ2: 設定クラスに追加

```python
# app/core/saml_config.py に追加

class SAMLSettings(BaseSettings):
    # 既存の設定...
    
    SAML_IDP_METADATA_URL: Optional[str] = None
    """SAML IdP メタデータURL（動的設定取得用）"""
    
    SAML_METADATA_CACHE_TTL_SECONDS: int = 3600
    """メタデータキャッシュの有効期限（秒）デフォルト: 1時間"""
    
    SAML_METADATA_AUTO_REFRESH: bool = True
    """証明書検証失敗時の自動再取得を有効化"""
```

### ステップ3: ヘルスチェックエンドポイントで検証

```python
# app/api/v1/endpoints/saml_auth.py

@router.get("/health", response_model=SAMLHealthCheckResponse)
async def saml_health_check(saml_service: SAMLServiceDep):
    """SAML設定とIdP接続性を確認"""
    
    # メタデータ検証
    metadata_valid = False
    metadata_error = None
    
    if saml_service.metadata_loader:
        metadata_valid, metadata_error = await saml_service.metadata_loader.validate_metadata()
    
    return SAMLHealthCheckResponse(
        status="healthy" if metadata_valid else "error",
        metadata_accessible=metadata_valid,
        metadata_error=metadata_error,
        # ...
    )
```

## 使用例

### Keycloakの場合

```bash
# .env
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor
```

このURLにアクセスすると、以下のようなXMLが返されます：

```xml
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="http://localhost:8090/realms/koiki-saml">
  <IDPSSODescriptor>
    <KeyDescriptor use="signing">
      <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
        <ds:X509Data>
          <ds:X509Certificate>
            MIICmzCCAYMCBgGU...（証明書データ）
          </ds:X509Certificate>
        </ds:X509Data>
      </ds:KeyInfo>
    </KeyDescriptor>
    <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                         Location="http://localhost:8090/realms/koiki-saml/protocol/saml"/>
  </IDPSSODescriptor>
</EntityDescriptor>
```

この証明書が自動的に抽出・使用されます。

### Azure AD (Entra ID)の場合

```bash
SAML_IDP_METADATA_URL=https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml
```

### Okta / Auth0 / OneLogin

各IdPは標準的なメタデータエンドポイントを提供しています：

```bash
# Okta
SAML_IDP_METADATA_URL=https://{your-domain}.okta.com/app/{app-id}/sso/saml/metadata

# Auth0
SAML_IDP_METADATA_URL=https://{your-domain}.auth0.com/samlp/metadata/{connection}

# OneLogin
SAML_IDP_METADATA_URL=https://{subdomain}.onelogin.com/saml/metadata/{app-id}
```

## 比較：OIDC vs SAML（動的取得）

| 項目 | OIDC | SAML（動的メタデータ） |
|-----|------|---------------------|
| 設定の簡潔さ | ✅ `.well-known/openid-configuration` | ✅ `/protocol/saml/descriptor` |
| 証明書の自動取得 | ✅ JWKS | ✅ X.509 from metadata |
| 鍵ローテーション | ✅ 自動対応 | ✅ 自動対応 |
| キャッシュ戦略 | ✅ あり | ✅ あり |
| 事前設定 | ❌ 不要 | ❌ 不要 |
| エンタープライズ対応 | ✅ | ✅ |

## セキュリティ考慮事項

1. **メタデータURLの検証**
   - HTTPS使用を推奨
   - 開発環境のみHTTPを許可

2. **キャッシュ戦略**
   - デフォルト1時間（調整可能）
   - 署名検証失敗時に自動再取得

3. **証明書検証**
   - X.509証明書の有効期限チェック（オプション実装可）
   - 複数証明書のサポート（鍵ローテーション中）

4. **エラーハンドリング**
   - メタデータ取得失敗時はフォールバック（静的設定）
   - ヘルスチェックで定期的な可用性確認

## まとめ

**結論：SAMLでも動的メタデータ取得により、証明書の事前設定を回避できます**

- ✅ OIDCと同等の利便性を実現
- ✅ IdPメタデータURLの指定のみで動作
- ✅ 証明書ローテーションに自動対応
- ✅ エンタープライズ環境でも使用可能

この方式を採用することで、SAML認証もOIDCと同様に**運用負荷を大幅に削減**できます。
