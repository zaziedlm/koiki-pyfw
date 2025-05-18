# src/schemas/role.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Permissionスキーマのインポート (循環参照を避けるため .permission は使わない)
# from .permission import PermissionResponseSimple # __init__.py で管理

# --- Base Schema ---
class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, description="Name of the role (e.g., admin, editor)")
    description: Optional[str] = Field(None, description="Description of the role")

# --- Request Schemas ---
class RoleCreate(RoleBase):
    permission_ids: List[int] = Field([], description="List of permission IDs to assign to this role")

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None)
    permission_ids: Optional[List[int]] = Field(None, description="Replace assigned permissions with this list of IDs")

# --- Response Schemas ---
# 他のスキーマから参照されるシンプルなレスポンス
class RoleResponseSimple(BaseModel): # user.py で定義済みだが、こちらにも定義
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

# 完全な情報を含むレスポンス
class RoleResponse(RoleBase):
    id: int = Field(..., description="Unique ID of the role")
    created_at: datetime
    updated_at: datetime
    permissions: List["PermissionResponseSimple"] = Field([], description="Permissions associated with this role") # 権限情報も含む

    class Config:
        orm_mode = True

# --- RoleResponse の Forward Ref を解決 ---
# from .permission import PermissionResponseSimple # __init__.pyで解決されるはず
# RoleResponse.update_forward_refs() # Pydantic v1
# Pydantic v2では update_forward_refs は不要
from libkoiki.schemas.permission import PermissionResponseSimple # 明示的にインポート
RoleResponse.model_rebuild() # Pydantic v2
