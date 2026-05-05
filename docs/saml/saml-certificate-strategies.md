# SAML証明書取得の柔軟な戦略設定ガイド

## 概要

現行 KOIKI-FW リポジトリ内の SAML backend 実装は `components/koiki_ref_app/src/koiki_ref_app/` 配下にあります。
本文中の実装コード例では `koiki_ref_app.*` を正規導線として扱います。
古い資料や移植先向け説明に残る `app.*` は、root `app/` 互換 wrapper または移植先プロジェクト例です。

エンタープライズ環境では、お客様のSSO環境やセキュリティポリシーに応じて、
動的メタデータ取得と静的証明書設定の両方をサポートする必要があります。

本システムは**4つの証明書取得戦略**を提供し、環境に応じて柔軟に切り替えられます。

## 証明書取得戦略の種類

### 1. **`auto`（推奨・デフォルト）**

メタデータURLを優先し、失敗時は静的証明書にフォールバック。

```bash
# .env
SAML_CERT_FETCH_STRATEGY=auto

# メタデータURL（優先）
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor

# 静的証明書（フォールバック用）
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
MIICmzCCAYMCBgGU...
-----END CERTIFICATE-----"
```

**動作:**
1. ✅ メタデータURLから証明書を取得
2. ❌ 失敗した場合 → 静的証明書を使用
3. 🔄 署名検証エラー時は自動的にメタデータを再取得

**適用シーン:**
- 💼 **最も推奨される設定**
- 通常運用ではメタデータを使用し、IdPダウン時にもサービス継続
- 開発環境から本番環境への移行期間

---

### 2. **`metadata`（モダン環境）**

メタデータURLのみを使用。静的証明書は無視。

```bash
# .env
SAML_CERT_FETCH_STRATEGY=metadata
SAML_IDP_METADATA_URL=https://sso.example.com/saml/metadata

# 以下は不要（設定しても無視される）
# SAML_IDP_X509_CERT=...
# SAML_IDP_ENTITY_ID=...
# SAML_IDP_SSO_URL=...
```

**動作:**
1. ✅ メタデータURLから証明書・エンティティID・SSO URLを自動取得
2. ❌ メタデータ取得失敗 → エラー（フォールバックなし）
3. 🔄 1時間ごとにキャッシュ更新

**適用シーン:**
- ☁️ クラウドIdP環境（Okta, Azure AD, Auth0など）
- 🔒 証明書ローテーションが頻繁な環境
- 🆕 新規構築プロジェクト

**メリット:**
- 設定が最もシンプル
- 証明書の有効期限切れのリスクなし
- OIDCと同等の運用性

---

### 3. **`static`（レガシー環境）**

静的証明書のみを使用。メタデータURLは無視。

```bash
# .env
SAML_CERT_FETCH_STRATEGY=static

# 必須設定
SAML_IDP_ENTITY_ID=https://customer-idp.example.com
SAML_IDP_SSO_URL=https://customer-idp.example.com/saml/sso
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
MIICmzCCAYMCBgGU...
-----END CERTIFICATE-----"

# 以下は使用されない
# SAML_IDP_METADATA_URL=...
```

**動作:**
1. ✅ 環境変数から証明書を直接読み込み
2. ❌ 証明書更新時は手動で再設定が必要
3. ⚠️ 自動リフレッシュ機能なし

**適用シーン:**
- 🏢 オンプレミスIdP（メタデータエンドポイント未実装）
- 🔐 エアギャップ環境（外部通信不可）
- 📜 お客様から証明書を直接提供される場合
- 🏛️ レガシーSAML実装（SAML 1.1など）

**注意点:**
- 証明書の有効期限管理が必要
- IdP側の証明書更新時に手動対応が必須

---

### 4. **`hybrid`（マルチIdP環境）**

両方の方式を試行。メタデータ優先、失敗時は静的証明書。

```bash
# .env
SAML_CERT_FETCH_STRATEGY=hybrid

# 両方設定
SAML_IDP_METADATA_URL=https://primary-idp.example.com/metadata
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----..."
```

**動作:**
1. ✅ メタデータURLから取得を試行
2. ❌ 失敗した場合 → 静的証明書を使用
3. 🔄 署名検証エラー時は両方を再試行

**適用シーン:**
- 🌐 複数IdPを切り替える環境
- 🔄 IdP移行期間（旧IdPと新IdP併用）
- 🛡️ 高可用性が求められる環境

---

## 設定例：様々な環境パターン

### パターンA: Keycloak（開発環境）

```bash
# 動的メタデータ推奨
SAML_CERT_FETCH_STRATEGY=metadata
SAML_IDP_METADATA_URL=http://localhost:8090/realms/koiki-saml/protocol/saml/descriptor
SAML_METADATA_CACHE_TTL_SECONDS=1800  # 30分
```

### パターンB: Azure AD / Entra ID（本番環境）

```bash
# メタデータのみで完結
SAML_CERT_FETCH_STRATEGY=metadata
SAML_IDP_METADATA_URL=https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml
SAML_METADATA_CACHE_TTL_SECONDS=3600  # 1時間
SAML_SKIP_SSL_VERIFY=false  # 本番環境では必ずfalse
```

### パターンC: Okta（商用SaaS）

```bash
# Oktaは証明書ローテーションが頻繁なのでメタデータ推奨
SAML_CERT_FETCH_STRATEGY=metadata
SAML_IDP_METADATA_URL=https://{your-domain}.okta.com/app/{app-id}/sso/saml/metadata
SAML_METADATA_CACHE_TTL_SECONDS=3600
```

### パターンD: お客様独自IdP（オンプレミス）

```bash
# メタデータエンドポイントがない場合
SAML_CERT_FETCH_STRATEGY=static

SAML_IDP_ENTITY_ID=https://customer-sso.local/saml
SAML_IDP_SSO_URL=https://customer-sso.local/saml/sso
SAML_IDP_SLS_URL=https://customer-sso.local/saml/sls
SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
（お客様から提供された証明書をそのまま貼り付け）
-----END CERTIFICATE-----"
```

### パターンE: 高可用性環境（DR対策）

```bash
# 自動フォールバック設定
SAML_CERT_FETCH_STRATEGY=auto

# プライマリ: メタデータ
SAML_IDP_METADATA_URL=https://primary-idp.example.com/metadata

# セカンダリ: 静的証明書（バックアップ）
SAML_IDP_ENTITY_ID=https://backup-idp.example.com
SAML_IDP_SSO_URL=https://backup-idp.example.com/sso
SAML_IDP_X509_CERT="（バックアップIdPの証明書）"

# エラー時の自動リカバリー
SAML_METADATA_AUTO_REFRESH_ON_ERROR=true
```

### パターンF: IdP移行期間（新旧併用）

```bash
# 新IdPに移行中、旧IdPも併用
SAML_CERT_FETCH_STRATEGY=hybrid

# 新IdP（優先）
SAML_IDP_METADATA_URL=https://new-idp.example.com/metadata

# 旧IdP（フォールバック）
SAML_IDP_ENTITY_ID=https://old-idp.example.com
SAML_IDP_SSO_URL=https://old-idp.example.com/sso
SAML_IDP_X509_CERT="（旧IdPの証明書）"
```

---

## 実装コード例

### SAMLServiceでの使用

```python
# components/koiki_ref_app/src/koiki_ref_app/services/saml_service.py

from koiki_ref_app.services.saml_certificate_manager import SAMLCertificateManager

class SAMLService:
    def __init__(self, ...):
        self.cert_manager = SAMLCertificateManager(self.saml_settings)
    
    async def _build_saml_config(self, acs_url: str) -> Dict[str, Any]:
        """SAML設定を構築（証明書は動的取得）"""
        
        # 証明書を取得（戦略に応じて自動選択）
        idp_cert, cert_source = await self.cert_manager.get_signing_certificate()
        
        logger.info(
            "Building SAML config",
            cert_source=cert_source,
            strategy=self.cert_manager.strategy,
        )
        
        # メタデータから完全な設定を取得（可能な場合）
        if self.cert_manager.metadata_loader:
            idp_metadata = await self.cert_manager.get_idp_metadata()
            entity_id = idp_metadata["entity_id"]
            sso_url = idp_metadata["sso_url"]
        else:
            entity_id = self.saml_settings.SAML_IDP_ENTITY_ID
            sso_url = self.saml_settings.SAML_IDP_SSO_URL
        
        return {
            "sp": {...},
            "idp": {
                "entityId": entity_id,
                "singleSignOnService": {
                    "url": sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": idp_cert,
            },
        }
    
    async def process_saml_response(self, saml_response: str):
        """SAML Responseを検証（エラー時の自動リトライ）"""
        try:
            # 通常の署名検証
            auth.process_response()
            return auth.get_attributes()
        
        except Exception as e:
            if "signature" in str(e).lower():
                logger.warning(
                    "Signature verification failed, attempting certificate refresh",
                    error=str(e),
                )
                
                # 証明書を再取得して再試行
                new_cert, source = await self.cert_manager.refresh_on_verification_failure()
                
                # 新しい証明書で再構築
                saml_config = await self._build_saml_config(...)
                auth = OneLogin_Saml2_Auth(request_data, saml_config)
                auth.process_response()
                
                logger.info(
                    "Signature verification succeeded after refresh",
                    new_cert_source=source,
                )
                
                return auth.get_attributes()
            
            raise
```

### ヘルスチェックエンドポイント

```python
@router.get("/health")
async def saml_health_check(saml_service: SAMLServiceDep):
    """SAML証明書取得の状態を確認"""
    
    cert_info = saml_service.cert_manager.get_certificate_source_info()
    
    # 証明書取得テスト
    try:
        cert, source = await saml_service.cert_manager.get_signing_certificate()
        cert_available = True
        cert_error = None
    except Exception as e:
        cert_available = False
        cert_error = str(e)
    
    return {
        "status": "healthy" if cert_available else "error",
        "certificate_available": cert_available,
        "certificate_source": source if cert_available else None,
        "certificate_error": cert_error,
        **cert_info,
    }
```

---

## トラブルシューティング

### Q1: メタデータ取得が失敗する

```bash
# 一時的に静的証明書にフォールバック
SAML_CERT_FETCH_STRATEGY=auto  # または static

# デバッグモード有効化
SAML_DEBUG_MODE=true
SAML_SKIP_SSL_VERIFY=true  # 開発環境のみ
```

### Q2: 証明書が頻繁に更新される

```bash
# キャッシュ期間を短縮
SAML_METADATA_CACHE_TTL_SECONDS=600  # 10分

# 自動リフレッシュを有効化
SAML_METADATA_AUTO_REFRESH_ON_ERROR=true
```

### Q3: IdP移行時の対応

```bash
# 段階的移行プラン
# フェーズ1: hybrid戦略で両方設定
SAML_CERT_FETCH_STRATEGY=hybrid
SAML_IDP_METADATA_URL=https://new-idp.example.com/metadata
SAML_IDP_X509_CERT="（旧IdPの証明書）"

# フェーズ2: 新IdPのみに切り替え
SAML_CERT_FETCH_STRATEGY=metadata
SAML_IDP_METADATA_URL=https://new-idp.example.com/metadata
```

---

## まとめ

| 戦略 | 推奨環境 | 設定の簡潔さ | 柔軟性 | 運用負荷 |
|-----|---------|------------|-------|---------|
| **auto** | 汎用 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **metadata** | クラウド | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **static** | レガシー | ⭐⭐ | ⭐ | ⭐⭐ |
| **hybrid** | マルチIdP | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**推奨事項:**
1. 🆕 **新規構築**: `metadata` 戦略を推奨
2. 🏢 **エンタープライズ**: `auto` または `hybrid` で柔軟に対応
3. 🔧 **既存システム**: `static` から `auto` への段階的移行を検討
