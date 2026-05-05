import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

os.environ["DEBUG"] = "true"
os.environ["APP_ENV"] = "testing"

from koiki_ref_app.core.sso_config import SSOSettings
from koiki_ref_app.schemas.sso import SSOUserInfo
from koiki_ref_app.services.sso_service import SSOService
from libkoiki.core.exceptions import ValidationException


@pytest.fixture
def sso_settings() -> SSOSettings:
    return SSOSettings(
        SSO_CLIENT_ID="client-id",
        SSO_CLIENT_SECRET="client-secret",
        SSO_ISSUER_URL="https://issuer.example.com",
        SSO_JWKS_URI="https://issuer.example.com/.well-known/jwks.json",
        SSO_TOKEN_ENDPOINT="https://issuer.example.com/oauth/token",
        SSO_AUTHORIZATION_ENDPOINT="https://issuer.example.com/oauth/authorize",
        SSO_STATE_SIGNING_KEY="state-secret",
        SSO_ALLOWED_ALGORITHMS="RS256",
        SSO_STATE_TTL_SECONDS=600,
        SSO_DEFAULT_REDIRECT_URI="https://app.example.com/sso/callback",
        SSO_ALLOWED_REDIRECT_URIS="https://app.example.com/sso/callback",
    )


@pytest.fixture
def sso_service(sso_settings: SSOSettings) -> SSOService:
    return SSOService(
        user_service=MagicMock(),
        auth_service=MagicMock(),
        sso_settings=sso_settings,
    )


def test_validate_state_success(sso_service: SSOService, sso_settings: SSOSettings) -> None:
    context = sso_service.generate_authorization_context()

    # 例外が発生しないことを確認
    sso_service.validate_state(context["state"], context["nonce"])


def test_validate_state_nonce_mismatch(sso_service: SSOService, sso_settings: SSOSettings) -> None:
    context = sso_service.generate_authorization_context()

    with pytest.raises(ValidationException):
        sso_service.validate_state(context["state"], "different-nonce")


def test_validate_state_expired(sso_service: SSOService, sso_settings: SSOSettings) -> None:
    nonce = "nonce-value"
    issued_at = datetime.now(timezone.utc) - timedelta(seconds=sso_settings.SSO_STATE_TTL_SECONDS + 5)
    state_token, _ = sso_service._create_state_token(nonce, issued_at=issued_at)

    with pytest.raises(ValidationException):
        sso_service.validate_state(state_token, nonce)


def test_verify_at_hash_rs256() -> None:
    access_token = "SlAV32hkKG"
    digest = hashlib.sha256(access_token.encode("utf-8")).digest()
    at_hash = base64.urlsafe_b64encode(digest[: len(digest) // 2]).decode("ascii").rstrip("=")

    assert SSOService._verify_at_hash(access_token, at_hash, "RS256") is True


def test_verify_at_hash_unsupported_alg() -> None:
    assert SSOService._verify_at_hash("token", "hash", "RS123") is False


@patch("koiki_ref_app.services.sso_service.logger")
def test_generate_authorization_context_keeps_redirect_and_nonce_out_of_normal_logger(
    mock_logger,
    sso_service: SSOService,
) -> None:
    context = sso_service.generate_authorization_context()

    assert context["redirect_uri"] == "https://app.example.com/sso/callback"
    info_kwargs = [call.kwargs for call in mock_logger.info.call_args_list]
    assert info_kwargs
    assert all("redirect_uri" not in kwargs for kwargs in info_kwargs)
    assert all("nonce" not in kwargs for kwargs in info_kwargs)


@pytest.mark.asyncio
@patch("koiki_ref_app.services.sso_service.logger")
async def test_verify_id_token_success_keeps_identity_values_out_of_normal_logger(
    mock_logger,
    sso_service: SSOService,
) -> None:
    payload = {
        "sub": "subject-123",
        "email": "user@example.com",
        "email_verified": True,
        "nonce": "nonce-123",
        "aud": "client-id",
    }
    sso_service._verify_jwt_with_jwks = AsyncMock(return_value=(payload, "RS256"))
    sso_service._validate_state_token = MagicMock()

    user_info = await sso_service.verify_id_token(
        "id-token",
        expected_nonce="nonce-123",
        state_token="state-token",
    )

    assert user_info.email == "user@example.com"
    info_kwargs = [call.kwargs for call in mock_logger.info.call_args_list]
    assert info_kwargs
    assert all("email" not in kwargs for kwargs in info_kwargs)
    assert all("sub" not in kwargs for kwargs in info_kwargs)
    assert any(kwargs.get("email_verified") is True for kwargs in info_kwargs)


@pytest.mark.asyncio
@patch("koiki_ref_app.services.sso_service.logger")
async def test_authenticate_sso_user_keeps_email_and_sub_out_of_normal_logger(
    mock_logger,
    sso_service: SSOService,
) -> None:
    db = MagicMock()
    user = MagicMock()
    user.id = 42
    user.is_active = True

    user_info = SSOUserInfo(
        sub="subject-123",
        email="user@example.com",
        email_verified=True,
        name="Test User",
    )

    sso_service.user_sso_repository.get_by_sso_subject_id = AsyncMock(
        return_value=None
    )
    sso_service.user_sso_repository.create_sso_link = AsyncMock()
    sso_service.user_service.get_user_by_email = AsyncMock(return_value=user)

    result_user, _ = await sso_service.authenticate_sso_user(user_info, db)

    assert result_user is user
    info_kwargs = [call.kwargs for call in mock_logger.info.call_args_list]
    warning_kwargs = [call.kwargs for call in mock_logger.warning.call_args_list]
    assert all("email" not in kwargs for kwargs in info_kwargs + warning_kwargs)
    assert all("sub" not in kwargs for kwargs in info_kwargs + warning_kwargs)
    assert any(kwargs.get("user_id") == 42 for kwargs in info_kwargs)


@patch("koiki_ref_app.services.sso_service.logger")
def test_redirect_uri_not_allowed_keeps_redirect_value_out_of_normal_logger(
    mock_logger,
    sso_service: SSOService,
) -> None:
    sso_service.sso_settings.is_redirect_uri_allowed = MagicMock(return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        sso_service._ensure_redirect_uri_allowed("https://evil.example.com/callback")

    assert exc_info.value.status_code == 400
    warning_kwargs = [call.kwargs for call in mock_logger.warning.call_args_list]
    assert warning_kwargs
    assert all("redirect_uri" not in kwargs for kwargs in warning_kwargs)


@pytest.mark.asyncio
@patch("koiki_ref_app.services.sso_service.logger")
async def test_fetch_jwks_error_keeps_jwks_uri_out_of_normal_logger(
    mock_logger,
    sso_service: SSOService,
) -> None:
    class DummyClient:
        async def __aenter__(self):
            raise RuntimeError("network down")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("koiki_ref_app.services.sso_service.httpx.AsyncClient", return_value=DummyClient()):
        with pytest.raises(HTTPException) as exc_info:
            await sso_service._fetch_jwks(force_refresh=True)

    assert exc_info.value.status_code == 401
    error_kwargs = [call.kwargs for call in mock_logger.error.call_args_list]
    assert error_kwargs
    assert all("jwks_uri" not in kwargs for kwargs in error_kwargs)


@pytest.mark.asyncio
@patch("koiki_ref_app.services.sso_service.logger")
async def test_verify_id_token_unexpected_error_logs_error_type_only(
    mock_logger,
    sso_service: SSOService,
) -> None:
    sso_service._validate_state_token = MagicMock()
    sso_service._verify_jwt_with_jwks = AsyncMock(side_effect=RuntimeError("secret detail"))

    with pytest.raises(HTTPException) as exc_info:
        await sso_service.verify_id_token(
            "id-token",
            expected_nonce="nonce-123",
            state_token="state-token",
        )

    assert exc_info.value.status_code == 500
    error_kwargs = mock_logger.error.call_args.kwargs
    assert error_kwargs["error_type"] == "RuntimeError"
    assert "error" not in error_kwargs


@pytest.mark.asyncio
@patch("koiki_ref_app.services.sso_service.logger")
async def test_create_internal_token_pair_failure_logs_error_type_only(
    mock_logger,
    sso_service: SSOService,
) -> None:
    mock_user = MagicMock()
    mock_user.id = 99
    mock_db = MagicMock()
    sso_service.auth_service.create_token_pair = AsyncMock(side_effect=RuntimeError("token secret"))

    with pytest.raises(HTTPException) as exc_info:
        await sso_service.create_internal_token_pair(mock_user, mock_db)

    assert exc_info.value.status_code == 500
    error_kwargs = mock_logger.error.call_args.kwargs
    assert error_kwargs["user_id"] == 99
    assert error_kwargs["error_type"] == "RuntimeError"
    assert "error" not in error_kwargs
