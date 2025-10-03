# app/services/saml_metadata_loader.py
"""SAML IdPメタデータ動的取得サービス"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx
import structlog

logger = structlog.get_logger(__name__)


class SAMLMetadataLoader:
    """
    SAML IdPメタデータを動的に取得・キャッシュするクラス

    OIDCのJWKS取得と同様の動的メタデータ取得を実現:
    - IdPメタデータURLからXMLを取得
    - X.509証明書を抽出
    - 署名検証用の証明書をキャッシュ
    - 証明書の有効期限チェック（オプション）
    """

    # SAML 2.0 名前空間
    NS = {
        "md": "urn:oasis:names:tc:SAML:2.0:metadata",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
    }

    def __init__(
        self,
        metadata_url: str,
        cache_ttl_seconds: int = 3600,
        ssl_verify: bool = True,
        timeout_seconds: int = 10,
    ):
        """
        Args:
            metadata_url: IdPメタデータのURL
            cache_ttl_seconds: キャッシュ有効期限（秒）
            ssl_verify: SSL証明書の検証を行うか
            timeout_seconds: HTTPリクエストタイムアウト
        """
        self.metadata_url = metadata_url
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.ssl_verify = ssl_verify
        self.timeout = timeout_seconds

        # キャッシュ
        self._cached_metadata: Optional[str] = None
        self._cached_certs: Optional[Dict[str, str]] = None
        self._cache_expires_at: Optional[datetime] = None

        self._validate_metadata_url()

    def _validate_metadata_url(self) -> None:
        """メタデータURLの基本的な検証"""
        parsed = urlparse(self.metadata_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid metadata URL: {self.metadata_url}")

        if not self.ssl_verify and parsed.scheme == "https":
            logger.warning(
                "SSL verification disabled for SAML metadata",
                url=self.metadata_url,
            )

    async def get_metadata_xml(self, force_refresh: bool = False) -> str:
        """
        IdPメタデータXMLを取得（キャッシュあり）

        Args:
            force_refresh: キャッシュを無視して強制的に再取得

        Returns:
            メタデータXML文字列

        Raises:
            httpx.HTTPError: メタデータ取得失敗
            ValueError: 無効なXML
        """
        now = datetime.now(timezone.utc)

        # キャッシュチェック
        if (
            not force_refresh
            and self._cached_metadata
            and self._cache_expires_at
            and now < self._cache_expires_at
        ):
            logger.debug(
                "Using cached SAML metadata",
                expires_in=(self._cache_expires_at - now).total_seconds(),
            )
            return self._cached_metadata

        # メタデータ取得
        logger.info("Fetching SAML IdP metadata", url=self.metadata_url)

        async with httpx.AsyncClient(verify=self.ssl_verify) as client:
            response = await client.get(
                self.metadata_url,
                timeout=self.timeout,
                headers={"Accept": "application/samlmetadata+xml, application/xml"},
            )
            response.raise_for_status()

            metadata_xml = response.text

            # 簡易的なXML検証
            try:
                ET.fromstring(metadata_xml)
            except ET.ParseError as e:
                logger.error("Invalid XML in SAML metadata", error=str(e))
                raise ValueError(f"Invalid SAML metadata XML: {e}")

            # キャッシュ更新
            self._cached_metadata = metadata_xml
            self._cache_expires_at = now + self.cache_ttl
            self._cached_certs = None  # 証明書キャッシュもクリア

            logger.info(
                "SAML metadata fetched successfully",
                cache_ttl=self.cache_ttl.total_seconds(),
            )

            return metadata_xml

    async def get_signing_certificates(
        self, force_refresh: bool = False
    ) -> Dict[str, str]:
        """
        署名検証用のX.509証明書を取得

        Args:
            force_refresh: キャッシュを無視して強制的に再取得

        Returns:
            証明書辞書 {use: certificate_pem}
            例: {"signing": "-----BEGIN CERTIFICATE-----\n..."}

        Raises:
            ValueError: 証明書が見つからない
        """
        # 証明書キャッシュチェック
        now = datetime.now(timezone.utc)
        if (
            not force_refresh
            and self._cached_certs
            and self._cache_expires_at
            and now < self._cache_expires_at
        ):
            logger.debug("Using cached SAML certificates")
            return self._cached_certs

        # メタデータから証明書を抽出
        metadata_xml = await self.get_metadata_xml(force_refresh)
        root = ET.fromstring(metadata_xml)

        certificates = {}

        # IDPSSODescriptor内のKeyDescriptorを検索
        idp_descriptors = root.findall(".//md:IDPSSODescriptor", self.NS)

        for idp_desc in idp_descriptors:
            key_descriptors = idp_desc.findall("md:KeyDescriptor", self.NS)

            for key_desc in key_descriptors:
                use = key_desc.get("use", "signing")  # デフォルトはsigning

                # X509Certificate要素を検索
                cert_elem = key_desc.find(".//ds:X509Certificate", self.NS)

                if cert_elem is not None and cert_elem.text:
                    cert_data = cert_elem.text.strip()
                    # PEM形式に整形
                    cert_pem = f"-----BEGIN CERTIFICATE-----\n{cert_data}\n-----END CERTIFICATE-----"
                    certificates[use] = cert_pem

                    logger.debug(
                        "Extracted certificate from SAML metadata",
                        use=use,
                        cert_length=len(cert_data),
                    )

        if not certificates:
            raise ValueError("No signing certificates found in SAML metadata")

        # キャッシュ更新
        self._cached_certs = certificates
        logger.info(
            "SAML certificates extracted",
            cert_count=len(certificates),
            uses=list(certificates.keys()),
        )

        return certificates

    async def get_idp_entity_id(self) -> str:
        """IdPのエンティティIDを取得"""
        metadata_xml = await self.get_metadata_xml()
        root = ET.fromstring(metadata_xml)

        entity_id = root.get("entityID")
        if not entity_id:
            raise ValueError("entityID not found in SAML metadata")

        return entity_id

    async def get_sso_service_url(self, binding: str = "redirect") -> Optional[str]:
        """
        シングルサインオンサービスのURLを取得

        Args:
            binding: "redirect" または "post"

        Returns:
            SSO service URL または None
        """
        metadata_xml = await self.get_metadata_xml()
        root = ET.fromstring(metadata_xml)

        # バインディングURN
        binding_urns = {
            "redirect": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            "post": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        }

        binding_urn = binding_urns.get(binding)
        if not binding_urn:
            raise ValueError(f"Unknown binding: {binding}")

        # SingleSignOnService要素を検索
        sso_services = root.findall(
            ".//md:IDPSSODescriptor/md:SingleSignOnService", self.NS
        )

        for sso_service in sso_services:
            if sso_service.get("Binding") == binding_urn:
                return sso_service.get("Location")

        return None

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._cached_metadata = None
        self._cached_certs = None
        self._cache_expires_at = None
        logger.info("SAML metadata cache cleared")

    async def validate_metadata(self) -> Tuple[bool, Optional[str]]:
        """
        メタデータの妥当性を検証

        Returns:
            (is_valid, error_message)
        """
        try:
            # メタデータ取得を強制リフレッシュ
            await self.get_metadata_xml(force_refresh=True)
            certificates = await self.get_signing_certificates(force_refresh=True)
            entity_id = await self.get_idp_entity_id()
            sso_url = await self.get_sso_service_url()

            if not entity_id:
                return False, "entityID not found"

            if not sso_url:
                return False, "SSO service URL not found"

            if not certificates:
                return False, "No signing certificates found"

            logger.info(
                "SAML metadata validated successfully",
                entity_id=entity_id,
                sso_url=sso_url,
                cert_count=len(certificates),
            )

            return True, None

        except Exception as e:
            logger.error("SAML metadata validation failed", error=str(e))
            return False, str(e)
