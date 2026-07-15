"""Periodic cleanup for authentication-related transient and history data."""

from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.repositories.login_attempt_repository import LoginAttemptRepository
from libkoiki.repositories.password_reset_repository import PasswordResetRepository
from libkoiki.repositories.refresh_token_repository import RefreshTokenRepository
from koiki_ref_app.repositories.saml_auth_flow_repository import SamlAuthFlowRepository


async def cleanup_auth_data(
    session: AsyncSession,
    *,
    login_attempt_retention_days: int,
    saml_terminal_flow_retention_days: int,
) -> Dict[str, int]:
    """Apply the configured retention policy once and return affected row counts.

    Repository cleanup methods own their existing transaction behavior.  All
    operations are idempotent, so a later periodic run safely retries an
    operation if another cleanup step fails.
    """
    login_attempts = LoginAttemptRepository()
    refresh_tokens = RefreshTokenRepository()
    password_reset_tokens = PasswordResetRepository()
    saml_flows = SamlAuthFlowRepository()

    for repository in (login_attempts, refresh_tokens, password_reset_tokens):
        repository.set_session(session)

    counts = {
        "login_attempts": await login_attempts.cleanup_old_attempts(
            days=login_attempt_retention_days
        ),
        "refresh_tokens": await refresh_tokens.cleanup_expired_tokens(),
        "password_reset_tokens": await password_reset_tokens.cleanup_expired_tokens(),
        "saml_active_flows": await saml_flows.expire_active_flows(session),
        "saml_terminal_flows": await saml_flows.delete_terminal_flows(
            session,
            retention_days=saml_terminal_flow_retention_days,
        ),
    }
    await session.commit()
    return counts
