from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from koiki_ref_app.bootstrap import bootstrap_orm
from koiki_ref_app.models.saml_auth_flow import SamlAuthFlow
from koiki_ref_app.repositories.saml_auth_flow_repository import SamlAuthFlowRepository
from libkoiki.db.base import Base


@pytest.mark.asyncio
async def test_saml_cleanup_uses_status_specific_expiry_and_retains_recent_terminal_flows():
    bootstrap_orm()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            session.add_all(
                [
                    SamlAuthFlow(
                        relay_nonce="expired-request",
                        status="authn_requested",
                        relay_expires_at=now - timedelta(seconds=1),
                    ),
                    SamlAuthFlow(
                        relay_nonce="active-request",
                        status="authn_requested",
                        relay_expires_at=now + timedelta(seconds=1),
                    ),
                    SamlAuthFlow(
                        relay_nonce="expired-ticket",
                        status="acs_verified",
                        login_ticket_expires_at=now - timedelta(seconds=1),
                    ),
                    SamlAuthFlow(
                        relay_nonce="active-ticket",
                        status="acs_verified",
                        login_ticket_expires_at=now + timedelta(seconds=1),
                    ),
                    SamlAuthFlow(
                        relay_nonce="old-terminal",
                        status="ticket_consumed",
                        updated_at=now - timedelta(days=31),
                    ),
                    SamlAuthFlow(
                        relay_nonce="recent-terminal",
                        status="expired",
                        updated_at=now - timedelta(days=29),
                    ),
                ]
            )
            await session.commit()

            repository = SamlAuthFlowRepository()
            assert await repository.expire_active_flows(session, now=now) == 2
            assert await repository.delete_terminal_flows(
                session,
                retention_days=30,
                now=now,
            ) == 1
            await session.commit()

            flows = {
                flow.relay_nonce: flow
                for flow in (await session.execute(select(SamlAuthFlow))).scalars()
            }

            assert flows["expired-request"].status == "expired"
            assert flows["expired-ticket"].status == "expired"
            assert flows["active-request"].status == "authn_requested"
            assert flows["active-ticket"].status == "acs_verified"
            assert "old-terminal" not in flows
            assert flows["recent-terminal"].status == "expired"
    finally:
        await engine.dispose()
