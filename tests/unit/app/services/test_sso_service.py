import base64
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.core.sso_config import SSOSettings
from app.services.sso_service import SSOService
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
