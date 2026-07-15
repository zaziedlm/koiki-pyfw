from koiki_ref_app.bootstrap import bootstrap_orm
from libkoiki.db.base import Base


def test_vnext_metadata_uses_owned_table_names_only() -> None:
    """M1 registers exactly the KOIKI-FW-managed vNext tables."""
    bootstrap_orm()

    assert set(Base.metadata.tables) == {
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


def test_vnext_metadata_excludes_external_user_table() -> None:
    """The downstream-owned quoted user table remains outside framework metadata."""
    bootstrap_orm()

    assert "user" not in Base.metadata.tables
