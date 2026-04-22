# app/api/__init__.py
"""app.api package.

Package initializer for API routing. Exposes versioned API routers for
external import and mounting by the application.
All module-level routers should be exported from here.
"""

from .v1 import router as v1_router

__all__ = ["v1_router"]
