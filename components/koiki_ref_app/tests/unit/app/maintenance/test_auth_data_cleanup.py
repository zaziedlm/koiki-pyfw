from unittest.mock import AsyncMock, Mock, patch

import pytest

from koiki_ref_app.maintenance.auth_data_cleanup import cleanup_auth_data


@pytest.mark.asyncio
@patch("koiki_ref_app.maintenance.auth_data_cleanup.SamlAuthFlowRepository")
@patch("koiki_ref_app.maintenance.auth_data_cleanup.PasswordResetRepository")
@patch("koiki_ref_app.maintenance.auth_data_cleanup.RefreshTokenRepository")
@patch("koiki_ref_app.maintenance.auth_data_cleanup.LoginAttemptRepository")
async def test_cleanup_auth_data_applies_all_configured_retention_paths(
    login_attempt_repository,
    refresh_token_repository,
    password_reset_repository,
    saml_auth_flow_repository,
):
    session = Mock()
    session.commit = AsyncMock()
    login_attempt_repository.return_value.cleanup_old_attempts = AsyncMock(return_value=1)
    refresh_token_repository.return_value.cleanup_expired_tokens = AsyncMock(return_value=2)
    password_reset_repository.return_value.cleanup_expired_tokens = AsyncMock(return_value=3)
    saml_auth_flow_repository.return_value.expire_active_flows = AsyncMock(return_value=4)
    saml_auth_flow_repository.return_value.delete_terminal_flows = AsyncMock(return_value=5)

    counts = await cleanup_auth_data(
        session,
        login_attempt_retention_days=45,
        saml_terminal_flow_retention_days=60,
    )

    assert counts == {
        "login_attempts": 1,
        "refresh_tokens": 2,
        "password_reset_tokens": 3,
        "saml_active_flows": 4,
        "saml_terminal_flows": 5,
    }
    login_attempt_repository.return_value.cleanup_old_attempts.assert_awaited_once_with(
        days=45
    )
    saml_auth_flow_repository.return_value.delete_terminal_flows.assert_awaited_once_with(
        session,
        retention_days=60,
    )
    session.commit.assert_awaited_once()
