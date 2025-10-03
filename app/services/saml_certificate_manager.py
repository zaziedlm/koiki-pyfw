# app/services/saml_certificate_manager.py
"""
SAML証明書マネージャー - 柔軟な証明書取得戦略

動的メタデータ取得と静的証明書設定の両方をサポートし、
環境に応じて自動的に切り替える統合マネージャー。
"""

from typing import Dict, Optional, Tuple

import structlog

from app.core.saml_config import SAMLSettings
from app.services.saml_metadata_loader import SAMLMetadataLoader

logger = structlog.get_logger(__name__)


class CertificateSource:
    """証明書の取得元を示す列挙型"""

    METADATA = "metadata"  # 動的メタデータから取得
    STATIC = "static"  # 静的設定から取得
    CACHE = "cache"  # キャッシュから取得


class SAMLCertificateManager:
    """
    SAML証明書取得の統合マネージャー

    複数の証明書取得戦略をサポート:
    1. 動的メタデータ取得（推奨）
    2. 静的X.509証明書設定（レガシー/特殊環境）
    3. ハイブリッド（両方を併用）
    4. 自動フォールバック

    使用例:
        ```python
        manager = SAMLCertificateManager(saml_settings)

        # 証明書取得（戦略に応じて自動選択）
        cert, source = await manager.get_signing_certificate()

        # エラー時の自動リトライ
        if signature_verification_failed:
            cert, source = await manager.get_signing_certificate(force_refresh=True)
        ```
    """

    def __init__(self, saml_settings: SAMLSettings):
        """
        Args:
            saml_settings: SAML設定オブジェクト
        """
        self.settings = saml_settings
        self.strategy = saml_settings.get_cert_strategy()

        # メタデータローダー（必要に応じて初期化）
        self.metadata_loader: Optional[SAMLMetadataLoader] = None
        if saml_settings.should_use_metadata():
            self.metadata_loader = SAMLMetadataLoader(
                metadata_url=saml_settings.SAML_IDP_METADATA_URL,
                cache_ttl_seconds=saml_settings.SAML_METADATA_CACHE_TTL_SECONDS,
                ssl_verify=not saml_settings.SAML_SKIP_SSL_VERIFY,
            )

        # 証明書キャッシュ（静的証明書用）
        self._static_cert_cache: Optional[str] = None
        self._last_cert_source: Optional[str] = None

        logger.info(
            "SAML Certificate Manager initialized",
            strategy=self.strategy,
            has_metadata_url=bool(saml_settings.SAML_IDP_METADATA_URL),
            has_static_cert=bool(saml_settings.SAML_IDP_X509_CERT),
        )

    async def get_signing_certificate(
        self, force_refresh: bool = False
    ) -> Tuple[str, str]:
        """
        署名検証用の証明書を取得

        設定された戦略に基づいて最適な方法で証明書を取得:
        - auto: メタデータ優先、失敗時は静的証明書にフォールバック
        - metadata: メタデータのみ
        - static: 静的証明書のみ
        - hybrid: メタデータを試し、失敗したら静的証明書

        Args:
            force_refresh: キャッシュを無視して強制的に再取得

        Returns:
            (certificate_pem, source)
            - certificate_pem: PEM形式の証明書文字列
            - source: 取得元 ("metadata", "static", "cache")

        Raises:
            ValueError: 証明書が取得できない場合
        """
        strategy = self.strategy

        logger.debug(
            "Fetching SAML signing certificate",
            strategy=strategy,
            force_refresh=force_refresh,
        )

        # 戦略に応じて取得
        if strategy == "metadata":
            return await self._get_from_metadata_only(force_refresh)

        elif strategy == "static":
            return self._get_from_static_only()

        elif strategy == "hybrid" or strategy == "auto":
            return await self._get_with_fallback(force_refresh)

        else:
            raise ValueError(f"Unknown certificate strategy: {strategy}")

    async def _get_from_metadata_only(
        self, force_refresh: bool = False
    ) -> Tuple[str, str]:
        """メタデータからのみ証明書を取得"""
        if not self.metadata_loader:
            raise ValueError(
                "Metadata URL is not configured but strategy is set to 'metadata'"
            )

        try:
            certificates = await self.metadata_loader.get_signing_certificates(
                force_refresh=force_refresh
            )

            # 'signing' 用途の証明書を優先、なければ最初の証明書
            cert = certificates.get("signing") or next(iter(certificates.values()))

            self._last_cert_source = CertificateSource.METADATA

            logger.info(
                "Certificate fetched from metadata",
                cert_count=len(certificates),
                uses=list(certificates.keys()),
            )

            return cert, CertificateSource.METADATA

        except Exception as e:
            logger.error(
                "Failed to fetch certificate from metadata",
                error=str(e),
                metadata_url=self.settings.SAML_IDP_METADATA_URL,
            )
            raise ValueError(f"Cannot fetch certificate from metadata: {e}")

    def _get_from_static_only(self) -> Tuple[str, str]:
        """静的設定からのみ証明書を取得"""
        if not self.settings.SAML_IDP_X509_CERT:
            raise ValueError(
                "Static certificate is not configured but strategy is set to 'static'"
            )

        cert = self._normalize_certificate(self.settings.SAML_IDP_X509_CERT)
        self._static_cert_cache = cert
        self._last_cert_source = CertificateSource.STATIC

        logger.info("Certificate loaded from static configuration")

        return cert, CertificateSource.STATIC

    async def _get_with_fallback(self, force_refresh: bool = False) -> Tuple[str, str]:
        """
        フォールバック付きで証明書を取得

        1. メタデータから取得を試みる
        2. 失敗した場合は静的証明書にフォールバック
        """
        # まずメタデータから試す
        if self.metadata_loader and self.settings.should_use_metadata():
            try:
                return await self._get_from_metadata_only(force_refresh)
            except Exception as e:
                logger.warning(
                    "Metadata fetch failed, falling back to static certificate",
                    error=str(e),
                )

        # フォールバック：静的証明書を使用
        if self.settings.should_use_static_cert():
            return self._get_from_static_only()

        # 両方とも利用不可
        raise ValueError(
            "No certificate available: neither metadata nor static certificate is configured"
        )

    async def refresh_on_verification_failure(self) -> Tuple[str, str]:
        """
        署名検証失敗時の自動リフレッシュ

        設定に応じて証明書を再取得:
        - メタデータ利用時: 強制的に再取得
        - 静的証明書のみ: そのまま返す（再取得不可）

        Returns:
            (certificate_pem, source)
        """
        if not self.settings.SAML_METADATA_AUTO_REFRESH_ON_ERROR:
            logger.info("Auto-refresh disabled, returning existing certificate")
            return await self.get_signing_certificate(force_refresh=False)

        logger.info("Verification failed, attempting to refresh certificate")

        # メタデータを使用している場合のみ再取得
        if self._last_cert_source == CertificateSource.METADATA:
            if self.metadata_loader:
                self.metadata_loader.clear_cache()
            return await self.get_signing_certificate(force_refresh=True)

        # 静的証明書の場合は再取得しても同じなのでそのまま
        logger.warning(
            "Cannot refresh static certificate, verification may continue to fail"
        )
        return await self.get_signing_certificate(force_refresh=False)

    async def get_idp_metadata(self) -> Dict[str, str]:
        """
        IdPの完全なメタデータを取得

        Returns:
            メタデータ辞書 {
                "entity_id": "...",
                "sso_url": "...",
                "sls_url": "...",  # オプション
                "certificate": "...",
            }
        """
        metadata = {}

        # メタデータから取得
        if self.metadata_loader:
            try:
                metadata["entity_id"] = await self.metadata_loader.get_idp_entity_id()
                metadata["sso_url"] = await self.metadata_loader.get_sso_service_url()

                cert, _ = await self.get_signing_certificate()
                metadata["certificate"] = cert

                logger.info("Complete IdP metadata fetched from metadata URL")
                return metadata

            except Exception as e:
                logger.warning(
                    "Failed to fetch complete metadata, using static config",
                    error=str(e),
                )

        # 静的設定から構築
        metadata["entity_id"] = self.settings.SAML_IDP_ENTITY_ID
        metadata["sso_url"] = self.settings.SAML_IDP_SSO_URL

        if self.settings.SAML_IDP_SLS_URL:
            metadata["sls_url"] = self.settings.SAML_IDP_SLS_URL

        cert, _ = await self.get_signing_certificate()
        metadata["certificate"] = cert

        logger.info("IdP metadata constructed from static configuration")
        return metadata

    def _normalize_certificate(self, cert: str) -> str:
        """
        証明書を正規化（PEM形式のヘッダー/フッター調整）

        Args:
            cert: 証明書文字列（ヘッダーあり/なし両方対応）

        Returns:
            正規化されたPEM形式の証明書
        """
        cert = cert.strip()

        # すでにPEM形式
        if cert.startswith("-----BEGIN CERTIFICATE-----"):
            return cert

        # Base64のみの場合、ヘッダー/フッターを追加
        cert_data = cert.replace("\n", "").replace("\r", "")
        return f"-----BEGIN CERTIFICATE-----\n{cert_data}\n-----END CERTIFICATE-----"

    def get_certificate_source_info(self) -> Dict[str, any]:
        """
        現在の証明書取得状態の情報を返す（デバッグ/ヘルスチェック用）

        Returns:
            状態情報辞書
        """
        return {
            "strategy": self.strategy,
            "last_source": self._last_cert_source,
            "metadata_available": bool(self.metadata_loader),
            "metadata_url": self.settings.SAML_IDP_METADATA_URL,
            "static_cert_configured": bool(self.settings.SAML_IDP_X509_CERT),
            "auto_refresh_enabled": self.settings.SAML_METADATA_AUTO_REFRESH_ON_ERROR,
            "cache_ttl_seconds": self.settings.SAML_METADATA_CACHE_TTL_SECONDS,
        }
