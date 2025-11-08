"""Web UI package for FastAPI dashboard views."""

from .router import router as web_router
from .auth_router import router as auth_router

__all__ = ["web_router", "auth_router"]
