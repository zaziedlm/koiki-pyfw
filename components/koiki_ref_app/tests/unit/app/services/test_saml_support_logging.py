import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def logging_setup(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    logging_module = importlib.reload(logging_module)
    logging_module.setup_logging()
    return logging_module


@pytest.fixture
def metadata_loader_module(logging_setup):
    del logging_setup
    module = importlib.import_module("app.services.saml_metadata_loader")
    return importlib.reload(module)


@pytest.fixture
def certificate_manager_module(logging_setup):
    del logging_setup
    module = importlib.import_module("app.services.saml_certificate_manager")
    return importlib.reload(module)


class TestSamlSupportLogging:
    @pytest.mark.asyncio
    async def test_metadata_loader_invalid_xml_logs_error_type_only(
        self,
        metadata_loader_module,
    ):
        loader = metadata_loader_module.SAMLMetadataLoader(
            metadata_url="https://idp.example.com/metadata.xml"
        )
        metadata_loader_module.logger = MagicMock()

        class DummyResponse:
            text = "<EntityDescriptor"

            def raise_for_status(self):
                return None

        class DummyClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def get(self, *args, **kwargs):
                return DummyResponse()

        metadata_loader_module.httpx.AsyncClient = MagicMock(return_value=DummyClient())

        with pytest.raises(ValueError):
            await loader.get_metadata_xml(force_refresh=True)

        error_kwargs = metadata_loader_module.logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "ParseError"
        assert "error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_metadata_loader_validate_metadata_logs_error_type_only(
        self,
        metadata_loader_module,
    ):
        loader = metadata_loader_module.SAMLMetadataLoader(
            metadata_url="https://idp.example.com/metadata.xml"
        )
        metadata_loader_module.logger = MagicMock()
        loader.get_metadata_xml = AsyncMock(side_effect=RuntimeError("metadata secret"))

        is_valid, message = await loader.validate_metadata()

        assert is_valid is False
        assert message == "metadata secret"
        error_kwargs = metadata_loader_module.logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_certificate_manager_metadata_failure_logs_error_type_only(
        self,
        certificate_manager_module,
    ):
        settings = SimpleNamespace(
            get_cert_strategy=lambda: "metadata",
            should_use_metadata=lambda: False,
            should_use_static_cert=lambda: False,
            SAML_IDP_METADATA_URL="https://idp.example.com/metadata.xml",
            SAML_METADATA_CACHE_TTL_SECONDS=3600,
            SAML_SKIP_SSL_VERIFY=False,
            SAML_IDP_X509_CERT=None,
        )
        manager = certificate_manager_module.SAMLCertificateManager(settings)
        certificate_manager_module.logger = MagicMock()
        manager.metadata_loader = SimpleNamespace(
            get_signing_certificates=AsyncMock(side_effect=RuntimeError("certificate secret"))
        )

        with pytest.raises(ValueError):
            await manager._get_from_metadata_only(force_refresh=True)

        error_kwargs = certificate_manager_module.logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_certificate_manager_fallback_warning_logs_error_type_only(
        self,
        certificate_manager_module,
    ):
        settings = SimpleNamespace(
            get_cert_strategy=lambda: "hybrid",
            should_use_metadata=lambda: True,
            should_use_static_cert=lambda: True,
            SAML_IDP_METADATA_URL="https://idp.example.com/metadata.xml",
            SAML_METADATA_CACHE_TTL_SECONDS=3600,
            SAML_SKIP_SSL_VERIFY=False,
            SAML_IDP_X509_CERT="CERTDATA",
        )
        manager = certificate_manager_module.SAMLCertificateManager(settings)
        certificate_manager_module.logger = MagicMock()
        manager.metadata_loader = SimpleNamespace()
        manager._get_from_metadata_only = AsyncMock(side_effect=RuntimeError("fallback secret"))

        cert, source = await manager._get_with_fallback(force_refresh=True)

        assert source == certificate_manager_module.CertificateSource.STATIC
        assert "CERTDATA" in cert
        warning_kwargs = certificate_manager_module.logger.warning.call_args.kwargs
        assert warning_kwargs["error_type"] == "RuntimeError"
        assert "error" not in warning_kwargs
