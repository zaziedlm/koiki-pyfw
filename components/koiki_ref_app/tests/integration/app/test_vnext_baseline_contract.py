"""PostgreSQL-only contract test for the single vNext Alembic baseline."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


EXPECTED_TABLES = {
    "koiki_users",
    "koiki_roles",
    "koiki_permissions",
    "koiki_user_roles",
    "koiki_role_permissions",
    "koiki_todos",
    "koiki_refresh_tokens",
    "koiki_password_reset_tokens",
    "koiki_login_attempts",
    "kkref_user_sso_links",
    "kkref_saml_auth_flows",
    "kkbiz_business_clock",
}

EXPECTED_INDEXES = {
    "koiki_todos": {"ix_koiki_todos_owner_id_created_at_desc"},
    "koiki_refresh_tokens": {
        "ix_koiki_refresh_tokens_user_id_created_at_desc",
        "ix_koiki_refresh_tokens_active_user_id_expires_at",
        "ix_koiki_refresh_tokens_expires_at",
    },
    "koiki_password_reset_tokens": {
        "ix_koiki_password_reset_tokens_user_id",
        "ix_koiki_password_reset_tokens_active_user_id_expires_at",
        "ix_koiki_password_reset_tokens_expires_at",
    },
    "koiki_login_attempts": {
        "ix_koiki_login_attempts_failed_email_attempted_at_desc",
        "ix_koiki_login_attempts_failed_ip_address_attempted_at_desc",
        "ix_koiki_login_attempts_success_email_attempted_at_desc",
        "ix_koiki_login_attempts_user_id",
        "ix_koiki_login_attempts_attempted_at",
    },
    "koiki_user_roles": {"ix_koiki_user_roles_role_id"},
    "koiki_role_permissions": {"ix_koiki_role_permissions_permission_id"},
    "kkref_user_sso_links": {
        "ix_kkref_user_sso_links_user_id_last_sso_login_desc",
        "ix_kkref_user_sso_links_sso_provider_last_sso_login_desc",
        "ix_kkref_user_sso_links_recent_last_sso_login_desc",
    },
    "kkref_saml_auth_flows": {
        "ix_kkref_saml_auth_flows_authn_requested_relay_expires_at",
        "ix_kkref_saml_auth_flows_acs_verified_login_ticket_expires_at",
        "ix_kkref_saml_auth_flows_terminal_updated_at",
        "ix_kkref_saml_auth_flows_user_id",
        "ix_kkref_saml_flows_consumed_user_updated",
    },
}

EXPECTED_UNIQUES = {
    "koiki_permissions": {"uq_koiki_permissions_name"},
    "koiki_roles": {"uq_koiki_roles_name"},
    "koiki_users": {"uq_koiki_users_username", "uq_koiki_users_email"},
    "koiki_refresh_tokens": {"uq_koiki_refresh_tokens_token_hash"},
    "koiki_password_reset_tokens": {"uq_koiki_password_reset_tokens_token_hash"},
    "kkref_user_sso_links": {
        "uq_kkref_user_sso_links_sso_subject_id_sso_provider",
        "uq_kkref_user_sso_links_user_id_sso_provider",
    },
    "kkref_saml_auth_flows": {
        "uq_kkref_saml_auth_flows_ticket_id",
        "uq_kkref_saml_auth_flows_relay_nonce",
    },
}

EXPECTED_PARTIAL_INDEX_TERMS = {
    ("koiki_refresh_tokens", "ix_koiki_refresh_tokens_active_user_id_expires_at"): (
        "is_revoked",
        "false",
    ),
    (
        "koiki_password_reset_tokens",
        "ix_koiki_password_reset_tokens_active_user_id_expires_at",
    ): ("is_used", "false"),
    ("koiki_login_attempts", "ix_koiki_login_attempts_failed_email_attempted_at_desc"): (
        "is_successful",
        "false",
    ),
    ("koiki_login_attempts", "ix_koiki_login_attempts_failed_ip_address_attempted_at_desc"): (
        "is_successful",
        "false",
    ),
    ("koiki_login_attempts", "ix_koiki_login_attempts_success_email_attempted_at_desc"): (
        "is_successful",
        "true",
    ),
    ("kkref_user_sso_links", "ix_kkref_user_sso_links_recent_last_sso_login_desc"): (
        "last_sso_login",
        "not null",
    ),
    ("kkref_saml_auth_flows", "ix_kkref_saml_auth_flows_authn_requested_relay_expires_at"): (
        "status",
        "authn_requested",
    ),
    ("kkref_saml_auth_flows", "ix_kkref_saml_auth_flows_acs_verified_login_ticket_expires_at"): (
        "status",
        "acs_verified",
    ),
    ("kkref_saml_auth_flows", "ix_kkref_saml_auth_flows_terminal_updated_at"): (
        "status",
        "expired",
        "ticket_consumed",
    ),
    ("kkref_saml_auth_flows", "ix_kkref_saml_flows_consumed_user_updated"): (
        "status",
        "ticket_consumed",
        "session_index",
        "not null",
    ),
}

REPO_ROOT = Path(__file__).resolve().parents[5]
ALEMBIC_INI = REPO_ROOT / "components" / "koiki_ref_app" / "alembic.ini"


def _baseline_url() -> str:
    url = os.getenv("BASELINE_CONTRACT_DATABASE_URL")
    if not url:
        pytest.skip("BASELINE_CONTRACT_DATABASE_URL is required for baseline DDL tests")
    if os.getenv("DATABASE_URL") != url:
        raise RuntimeError(
            "DATABASE_URL must equal BASELINE_CONTRACT_DATABASE_URL while running "
            "the destructive baseline contract test."
        )
    if make_url(url).database != "koiki_baseline_contract":
        raise RuntimeError(
            "Baseline contract tests only permit the dedicated "
            "koiki_baseline_contract database."
        )
    return url


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def _reset_public_schema(sync_url: str) -> None:
    engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
    finally:
        engine.dispose()


def _assert_fk(inspector, table: str, column: str, ondelete: str) -> None:
    foreign_key = next(
        fk
        for fk in inspector.get_foreign_keys(table)
        if fk["constrained_columns"] == [column]
    )
    assert foreign_key["options"].get("ondelete") == ondelete


@pytest.mark.integration
@pytest.mark.db_integration
def test_vnext_baseline_round_trip_and_postgresql_contract() -> None:
    database_url = _baseline_url()
    sync_url = database_url.replace("+asyncpg", "")
    _reset_public_schema(sync_url)
    config = _alembic_config()

    command.upgrade(config, "head")
    inspector = inspect(create_engine(sync_url))
    assert set(inspector.get_table_names()) == EXPECTED_TABLES | {"alembic_version"}

    for table in EXPECTED_TABLES:
        assert inspector.get_pk_constraint(table)["name"] == f"pk_{table}"
    for table, index_names in EXPECTED_INDEXES.items():
        assert index_names.issubset(
            {index["name"] for index in inspector.get_indexes(table)}
        )
    for table, unique_names in EXPECTED_UNIQUES.items():
        assert {unique["name"] for unique in inspector.get_unique_constraints(table)} == (
            unique_names
        )
    for (table, index_name), terms in EXPECTED_PARTIAL_INDEX_TERMS.items():
        index = next(index for index in inspector.get_indexes(table) if index["name"] == index_name)
        predicate = str(index["dialect_options"]["postgresql_where"]).lower()
        assert all(term in predicate for term in terms)

    assert {
        check["name"] for check in inspector.get_check_constraints("kkref_saml_auth_flows")
    } == {"ck_kkref_saml_auth_flows_valid_status"}
    assert {
        check["name"] for check in inspector.get_check_constraints("kkbiz_business_clock")
    } == {
        "ck_kkbiz_business_clock_singleton",
        "ck_kkbiz_business_clock_positive_version",
        "ck_kkbiz_business_clock_valid_mode",
        "ck_kkbiz_business_clock_frozen_value_pair",
    }
    _assert_fk(inspector, "koiki_todos", "owner_id", "CASCADE")
    _assert_fk(inspector, "koiki_refresh_tokens", "user_id", "CASCADE")
    _assert_fk(inspector, "koiki_password_reset_tokens", "user_id", "CASCADE")
    _assert_fk(inspector, "kkref_user_sso_links", "user_id", "CASCADE")
    _assert_fk(inspector, "koiki_login_attempts", "user_id", "SET NULL")
    _assert_fk(inspector, "kkref_saml_auth_flows", "user_id", "SET NULL")

    engine = create_engine(sync_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO koiki_users (username) VALUES ('baseline-user')")
            )
            user_id = connection.execute(
                text("SELECT id FROM koiki_users WHERE username = 'baseline-user'")
            ).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO koiki_todos (title, owner_id) "
                    "VALUES ('deleted with user', :user_id)"
                ),
                {"user_id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO koiki_login_attempts "
                    "(email, user_id, ip_address, is_successful) "
                    "VALUES ('user@example.com', :user_id, '127.0.0.1', false)"
                ),
                {"user_id": user_id},
            )
            connection.execute(text("DELETE FROM koiki_users WHERE id = :user_id"), {"user_id": user_id})
            assert connection.execute(text("SELECT count(*) FROM koiki_todos")).scalar_one() == 0
            assert connection.execute(
                text("SELECT user_id FROM koiki_login_attempts")
            ).scalar_one() is None

        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO kkref_saml_auth_flows (relay_nonce, status) "
                        "VALUES ('invalid-status', 'invalid')"
                    )
                )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO kkbiz_business_clock "
                        "(id, mode, base_timezone, offset_days, offset_minutes, version, updated_by) "
                        "VALUES (2, 'REALTIME', 'Asia/Tokyo', 0, 0, 1, 'contract-test')"
                    )
                )
    finally:
        engine.dispose()

    command.downgrade(config, "base")
    inspector = inspect(create_engine(sync_url))
    assert set(inspector.get_table_names()) == {"alembic_version"}
    command.upgrade(config, "head")
    inspector = inspect(create_engine(sync_url))
    assert EXPECTED_TABLES.issubset(inspector.get_table_names())
