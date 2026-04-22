"""Explicit ORM bootstrap for the KOIKI reference application."""

from __future__ import annotations

from sqlalchemy.orm import configure_mappers, relationship

from libkoiki.models.user import UserModel

_MODELS_LOADED = False
_MODEL_EXTENSIONS_REGISTERED = False


def load_app_models() -> None:
    """Import app-owned models so they are registered on shared metadata."""
    global _MODELS_LOADED
    if _MODELS_LOADED:
        return

    from koiki_ref_app.models.kkbiz import BusinessClock  # noqa: F401
    from koiki_ref_app.models.saml_auth_flow import SamlAuthFlow  # noqa: F401
    from koiki_ref_app.models.user_sso import UserSSO  # noqa: F401

    _MODELS_LOADED = True


def register_model_extensions() -> None:
    """Register app-owned relationships on framework models explicitly."""
    global _MODEL_EXTENSIONS_REGISTERED
    if _MODEL_EXTENSIONS_REGISTERED:
        return

    load_app_models()

    if not hasattr(UserModel, "sso_links"):
        UserModel.sso_links = relationship(
            "UserSSO",
            back_populates="user",
            cascade="all, delete-orphan",
            lazy="select",
        )

    _MODEL_EXTENSIONS_REGISTERED = True


def bootstrap_orm() -> None:
    """Load app models and finalize mapper configuration."""
    load_app_models()
    register_model_extensions()
    configure_mappers()

