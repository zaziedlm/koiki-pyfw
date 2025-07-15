# src/schemas/refresh_token.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RefreshTokenRequest(BaseModel):
    """リフレッシュトークンリクエスト"""
    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")

class TokenPairResponse(BaseModel):
    """トークンペアレスポンス（アクセストークン + リフレッシュトークン）"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

class RefreshTokenInfo(BaseModel):
    """リフレッシュトークン情報（管理用）"""
    id: int = Field(..., description="Refresh token ID")
    user_id: int = Field(..., description="Owner user ID")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    is_revoked: bool = Field(..., description="Whether the token is revoked")
    device_info: Optional[str] = Field(None, description="Device information")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    
    class Config:
        from_attributes = True