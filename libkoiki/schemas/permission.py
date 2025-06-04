# src/schemas/permission.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Base Schema ---
class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the permission (e.g., read:users, create:todos)")
    description: Optional[str] = Field(None, description="Description of the permission")

# --- Request Schemas ---
class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)

# --- Response Schemas ---
# 他のスキーマから参照されるシンプルなレスポンス
class PermissionResponseSimple(BaseModel): # user.py, role.py で定義済みだが、こちらにも定義
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

# 完全な情報を含むレスポンス
class PermissionResponse(PermissionBase):
    id: int = Field(..., description="Unique ID of the permission")
    created_at: datetime
    updated_at: datetime
    # roles: List["RoleResponseSimple"] = [] # この権限を持つロール一覧 (必要なら)

    class Config:
        orm_mode = True

# --- PermissionResponse の Forward Ref を解決 ---
# from .role import RoleResponseSimple # __init__.pyで解決されるはず
# PermissionResponse.update_forward_refs() # Pydantic v1
# Pydantic v2では不要
# from libkoiki.schemas.role import RoleResponseSimple # 明示的にインポート
# PermissionResponse.model_rebuild() # Pydantic v2
