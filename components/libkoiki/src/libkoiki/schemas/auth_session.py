from typing import Any

from pydantic import BaseModel, EmailStr, Field


class SessionLoginRequest(BaseModel):
    email: EmailStr | None = Field(None, description="User email address")
    username: str | None = Field(None, description="User email address or username")
    password: str = Field(..., min_length=1, description="User password")

    @property
    def login_identifier(self) -> str:
        return self.email or self.username or ""


class CSRFTokenResponse(BaseModel):
    message: str = "CSRF token generated"
    csrf_token: str
    header_name: str


class SessionAuthResponse(BaseModel):
    message: str
    user: dict[str, Any] | None = None
    location: str | None = None
