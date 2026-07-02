"""Schemas for the browser-session compatibility API."""

from pydantic import BaseModel


class BrowserSessionResponse(BaseModel):
    """Deliberately token-free response for browser authentication operations."""

    message: str
    expires_in: int | None = None
