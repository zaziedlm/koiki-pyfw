# src/schemas/todo.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# --- Base Schema ---
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the ToDo item")
    description: Optional[str] = Field(None, description="Optional description for the ToDo item")

# --- Request Schemas ---
class TodoCreate(TodoBase):
    # 作成時は is_completed は指定させない（デフォルトは False）
    pass

class TodoUpdate(BaseModel):
    # 更新時はすべてのフィールドを任意にする
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New title for the ToDo item")
    description: Optional[str] = Field(None, description="New description for the ToDo item")
    is_completed: Optional[bool] = Field(None, description="Completion status of the ToDo item")

# --- Response Schema ---
class TodoResponse(TodoBase):
    id: int = Field(..., description="Unique ID of the ToDo item")
    is_completed: bool = Field(..., description="Completion status")
    owner_id: int = Field(..., description="ID of the user who owns this ToDo")
    created_at: datetime = Field(..., description="Timestamp when the ToDo was created")
    updated_at: datetime = Field(..., description="Timestamp when the ToDo was last updated")

    class Config:
        orm_mode = True # SQLAlchemyモデルインスタンスから変換できるようにする