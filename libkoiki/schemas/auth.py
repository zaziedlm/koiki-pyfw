from pydantic import BaseModel, Field
from typing import Optional

class PasswordChangeRequest(BaseModel):
    """パスワード変更リクエスト"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 chars)")

class PasswordResetRequest(BaseModel):
    """パスワードリセット要求"""
    email: str = Field(..., description="Email address for password reset")

class PasswordResetConfirm(BaseModel):
    """パスワードリセット確認"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 chars)")

class AuthResponse(BaseModel):
    """認証系API共通レスポンス"""
    message: str = Field(..., description="Response message")
    user: Optional[dict] = Field(None, description="User information (if applicable)")
    data: Optional[dict] = Field(None, description="Additional response data")
