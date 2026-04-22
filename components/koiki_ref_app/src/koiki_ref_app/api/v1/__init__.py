# app/api/v1/__init__.py
"""API version 1 package.

Contains the version 1 API router and related endpoint modules.
Import the `router` object from this package to mount API v1 routes.
"""

from .router import router

__all__ = ["router"]
