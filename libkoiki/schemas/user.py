# src/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

# --- 相互参照のための前方参照 ---
# RoleResponseSimple / PermissionResponseSimple を先に定義 (または import .role / .permission)

class PermissionResponseSimple(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class RoleResponseSimple(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    # permissions: List[PermissionResponseSimple] = [] # ロールに紐づく権限も表示する場合

    class Config:
        from_attributes = True


# --- Base Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="User's username (unique identifier)")
    email: EmailStr = Field(..., description="User's email address (unique identifier)")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    is_active: bool = Field(True, description="Whether the user account is active") # デフォルト値を True に変更

# --- Request Schemas ---
class UserCreate(UserBase):
    # パスワードは作成時に必須、最小長8文字
    password: str = Field(..., min_length=8, max_length=100, description="User's password (min 8 chars)")

    # Pydanticレベルでの簡単なパスワード検証 (複雑性チェックはサービス層で行う)
    # @validator('password')
    # def password_validation(cls, v):
    #     if len(v) < 8:
    #         raise ValueError('Password must be at least 8 characters long')
    #     # 他の簡単なチェック (例: 空白を含まないか)
    #     if ' ' in v:
    #         raise ValueError('Password must not contain spaces')
    #     return v

class UserUpdate(BaseModel):
    # 更新時は必要なフィールドだけ送る想定なので、Baseを継承しない
    # 全てのフィールドをオプショナルにする
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username for the user")
    email: Optional[EmailStr] = Field(None, description="New email address for the user")
    full_name: Optional[str] = Field(None, max_length=255, description="New full name for the user")
    is_active: Optional[bool] = Field(None, description="Set user account active status")
    # パスワード更新も可能にする (任意)
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password (min 8 chars)")
    # is_superuser は管理者用APIで別途更新する想定 (ここでは含めない)

# --- Response Schemas ---
class UserResponse(UserBase):
    id: int = Field(..., description="Unique ID of the user")
    is_superuser: bool = Field(..., description="Whether the user has superuser privileges")
    created_at: datetime = Field(..., description="Timestamp when the user was created")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated")
    roles: List[RoleResponseSimple] = Field([], description="List of roles assigned to the user") # ロール情報を含める

    class Config:
        from_attributes = True # SQLAlchemyモデルから変換可能にする

# 詳細情報を含むレスポンススキーマ (必要に応じて)
# class UserDetailResponse(UserResponse):
#     # さらに詳細な情報 (例: 最終ログイン日時) を追加
#     last_login_at: Optional[datetime] = None