"""PostgreSQL integration coverage for vNext reference-application DB workflows."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from koiki_ref_app.models.kkbiz import BusinessClock
from koiki_ref_app.repositories.kkbiz.business_clock_repository import (
    BusinessClockRepository,
)
from koiki_ref_app.repositories.saml_auth_flow_repository import SamlAuthFlowRepository
from koiki_ref_app.repositories.user_sso_repository import UserSSORepository
from koiki_ref_app.services.kkbiz.business_clock_service import BusinessClockService
from libkoiki.models.user import UserModel
from libkoiki.models.permission import PermissionModel
from libkoiki.models.role import RoleModel
from libkoiki.repositories.password_reset_repository import PasswordResetRepository
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.services.password_reset_service import PasswordResetService


pytestmark = pytest.mark.asyncio


@pytest.mark.integration
@pytest.mark.db_integration
class TestVNextReferenceDatabaseWorkflows:
    async def test_password_reset_and_role_permission_relations(
        self, test_db_session: AsyncSession
    ) -> None:
        user = UserModel(username="security-workflow-user")
        role = RoleModel(name="security-workflow-role")
        permission = PermissionModel(name="read:security-workflow")
        role.permissions.append(permission)
        user.roles.append(role)
        test_db_session.add(user)
        await test_db_session.commit()

        user_repository = UserRepository()
        user_repository.set_session(test_db_session)
        loaded_user = await user_repository.get_user_with_roles_permissions(user.id)
        assert loaded_user is not None
        assert {
            assigned_permission.name
            for assigned_role in loaded_user.roles
            for assigned_permission in assigned_role.permissions
        } == {"read:security-workflow"}

        password_reset_service = PasswordResetService(PasswordResetRepository())
        reset_token, stored_token = await password_reset_service.create_reset_token(
            user,
            test_db_session,
            ip_address="127.0.0.1",
        )
        assert (await password_reset_service.validate_reset_token(reset_token, test_db_session)).id == (
            stored_token.id
        )
        assert (
            await password_reset_service.complete_password_reset(
                reset_token, "NewPassword123!", test_db_session
            )
        ).id == user.id
        await test_db_session.refresh(stored_token)
        assert stored_token.is_used is True

    async def test_sso_link_and_saml_ticket_lifecycle(
        self, test_db_session: AsyncSession
    ) -> None:
        user = UserModel(username="federated-workflow-user")
        test_db_session.add(user)
        await test_db_session.commit()

        sso_repository = UserSSORepository()
        sso_repository.set_session(test_db_session)
        first_link = await sso_repository.create_sso_link(
            user_id=user.id,
            sso_subject_id="subject-original",
            sso_provider="oidc",
        )
        updated_link = await sso_repository.create_sso_link(
            user_id=user.id,
            sso_subject_id="subject-updated",
            sso_provider="oidc",
        )
        await test_db_session.commit()
        assert updated_link.id == first_link.id
        assert len(await sso_repository.get_by_user_id(user.id, "oidc")) == 1

        saml_repository = SamlAuthFlowRepository()
        flow = await saml_repository.create_flow(
            test_db_session,
            request_id="request-workflow",
            relay_nonce="relay-workflow",
            relay_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        verified = await saml_repository.update_to_acs_verified(
            test_db_session,
            relay_nonce=flow.relay_nonce,
            user_id=user.id,
            subject_id="saml-subject",
            session_index="session-index-workflow",
            ticket_id="ticket-workflow",
            login_ticket_expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        assert verified is not None
        await test_db_session.commit()

        consumed = await saml_repository.consume_ticket_exclusive(
            test_db_session, "ticket-workflow"
        )
        assert consumed is not None
        await test_db_session.commit()
        assert (
            await saml_repository.consume_ticket_exclusive(
                test_db_session, "ticket-workflow"
            )
            is None
        )
        assert (
            await saml_repository.get_latest_session_index(test_db_session, user.id)
            == "session-index-workflow"
        )

    async def test_business_clock_recreates_singleton_and_rejects_second_row(
        self, test_db_session: AsyncSession
    ) -> None:
        service = BusinessClockService()
        initial = await service.kkbiz_get_clock(test_db_session)
        assert initial.id == 1

        repository = BusinessClockRepository()
        repository.set_session(test_db_session)
        await repository.delete(1)
        await test_db_session.commit()
        recreated = await service.kkbiz_get_clock(test_db_session)
        assert recreated.id == 1
        assert recreated.version == 1

        test_db_session.add(
            BusinessClock(
                id=2,
                mode="REALTIME",
                base_timezone="Asia/Tokyo",
                offset_days=0,
                offset_minutes=0,
                version=1,
                updated_by="integration-test",
            )
        )
        with pytest.raises(IntegrityError):
            await test_db_session.commit()
        await test_db_session.rollback()
        assert (
            await test_db_session.scalar(select(func.count()).select_from(BusinessClock))
            == 1
        )

    async def test_postgresql_catalog_has_no_invalid_or_duplicate_indexes(
        self, test_db_session: AsyncSession
    ) -> None:
        invalid_indexes = (
            await test_db_session.execute(
                text(
                    "SELECT indexrelid::regclass::text "
                    "FROM pg_index WHERE NOT indisvalid"
                )
            )
        ).scalars().all()
        duplicate_indexes = (
            await test_db_session.execute(
                text(
                    "SELECT array_agg(indexrelid::regclass::text ORDER BY indexrelid::regclass::text) "
                    "FROM pg_index "
                    "WHERE indrelid IN (SELECT oid FROM pg_class WHERE relnamespace = current_schema()::regnamespace) "
                    "GROUP BY indrelid, indkey, indpred, indexprs, indisunique, indisprimary "
                    "HAVING count(*) > 1"
                )
            )
        ).scalars().all()

        assert invalid_indexes == []
        assert duplicate_indexes == []
