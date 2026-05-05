from unittest.mock import AsyncMock, Mock, patch

import pytest

from koiki_ref_app.repositories.saml_auth_flow_repository import SamlAuthFlowRepository


class TestSamlAuthFlowRepositoryLogging:
    @pytest.mark.asyncio
    @patch("koiki_ref_app.repositories.saml_auth_flow_repository.logger")
    async def test_create_flow_does_not_log_request_or_nonce_fragments(self, mock_logger):
        repository = SamlAuthFlowRepository()
        db = Mock()
        added = {}

        def add_side_effect(flow):
            added["flow"] = flow

        async def flush_side_effect():
            added["flow"].id = 10

        db.add.side_effect = add_side_effect
        db.flush = AsyncMock(side_effect=flush_side_effect)

        flow = await repository.create_flow(
            db,
            request_id="ONELOGIN_request_value",
            relay_nonce="relay-nonce-secret",
            redirect_uri="https://frontend.example.com/saml/callback",
        )

        assert flow.id == 10
        log_kwargs = mock_logger.info.call_args.kwargs
        assert log_kwargs == {"flow_id": 10}

    @pytest.mark.asyncio
    @patch("koiki_ref_app.repositories.saml_auth_flow_repository.logger")
    async def test_update_to_acs_verified_does_not_log_nonce_or_ticket_fragments(
        self,
        mock_logger,
    ):
        repository = SamlAuthFlowRepository()
        repository.find_by_relay_nonce = AsyncMock()
        db = Mock()
        db.flush = AsyncMock()

        flow = Mock()
        flow.id = 11
        flow.status = "authn_requested"
        repository.find_by_relay_nonce.return_value = flow

        result = await repository.update_to_acs_verified(
            db,
            relay_nonce="relay-nonce-secret",
            user_id=1,
            subject_id="subject-123",
            session_index="session-123",
            ticket_id="ticket-secret",
            login_ticket_expires_at=Mock(),
        )

        assert result is flow
        flow.mark_acs_verified.assert_called_once()
        log_kwargs = mock_logger.info.call_args.kwargs
        assert log_kwargs == {"flow_id": 11}

    @pytest.mark.asyncio
    @patch("koiki_ref_app.repositories.saml_auth_flow_repository.logger")
    async def test_consume_ticket_exclusive_does_not_log_ticket_fragments(self, mock_logger):
        repository = SamlAuthFlowRepository()
        db = Mock()
        db.flush = AsyncMock()

        flow = Mock()
        flow.id = 12
        flow.status = "acs_verified"

        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = flow
        db.execute = AsyncMock(return_value=execute_result)

        result = await repository.consume_ticket_exclusive(db, "ticket-secret")

        assert result is flow
        flow.mark_ticket_consumed.assert_called_once()
        log_kwargs = mock_logger.info.call_args.kwargs
        assert log_kwargs == {"flow_id": 12}

    @pytest.mark.asyncio
    @patch("koiki_ref_app.repositories.saml_auth_flow_repository.logger")
    async def test_find_latest_session_index_logs_presence_only(self, mock_logger):
        repository = SamlAuthFlowRepository()
        db = Mock()

        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = "session-secret"
        db.execute = AsyncMock(return_value=execute_result)

        session_index = await repository.get_latest_session_index(db, user_id=7)

        assert session_index == "session-secret"
        log_kwargs = mock_logger.debug.call_args.kwargs
        assert log_kwargs == {"user_id": 7, "session_index_present": True}
