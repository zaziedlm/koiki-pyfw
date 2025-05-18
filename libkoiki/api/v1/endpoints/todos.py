# src/api/v1/endpoints/todos.py
from typing import List, Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter

from libkoiki.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from libkoiki.services.todo_service import TodoService
from libkoiki.api.dependencies import (
    TodoServiceDep,
    ActiveUserDep,
    # RateLimitDep, # ヘルパーを使う場合
)
from libkoiki.models.user import UserModel
from libkoiki.core.exceptions import ResourceNotFoundException, AuthorizationException
from libkoiki.core.logging import get_logger
from libkoiki.core.rate_limiter import limiter

logger = get_logger(__name__)
router = APIRouter()

# --- ToDo 作成 ---
@router.post(
    "/",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ToDo item for the current user",
    description="Creates a new ToDo item associated with the logged-in user.",
)
@limiter.limit("30/minute") # 例: 30回/分までに制限
async def create_todo(
    request: Request, # limiter用
    todo_in: TodoCreate,
    current_user: ActiveUserDep, # 認証済みアクティブユーザーを取得
    todo_service: TodoServiceDep,
) -> Any:
    """
    新しいToDo項目を作成します。

    - **title**: ToDoのタイトル (必須)
    - **description**: ToDoの説明 (任意)
    """
    logger.info("Creating new todo", user_id=current_user.id, title=todo_in.title)
    # サービスメソッドに owner_id を渡す
    new_todo = await todo_service.create_todo(todo_in=todo_in, owner_id=current_user.id)
    logger.info("Todo created successfully", todo_id=new_todo.id, user_id=current_user.id)
    return new_todo

# --- ログインユーザーのToDo一覧取得 ---
@router.get(
    "/",
    response_model=List[TodoResponse],
    summary="Get ToDo items for the current user",
    description="Retrieves a list of ToDo items belonging to the logged-in user.",
)
@limiter.limit("60/minute")
async def read_todos(
    request: Request, # limiter用
    current_user: ActiveUserDep,
    todo_service: TodoServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    現在のユーザーに紐づくToDo項目の一覧を取得します。

    - **skip**: スキップする件数 (ページネーション用)
    - **limit**: 取得する最大件数 (ページネーション用)
    """
    logger.debug("Fetching todos for user", user_id=current_user.id, skip=skip, limit=limit)
    todos = await todo_service.get_todos_by_owner(
        owner_id=current_user.id, skip=skip, limit=limit
    )
    logger.debug(f"Found {len(todos)} todos for user", user_id=current_user.id)
    return todos

# --- 特定のToDo取得 ---
@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Get a specific ToDo item",
    description="Retrieves a specific ToDo item by its ID, if it belongs to the logged-in user.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "ToDo item not found or does not belong to the user"},
    },
)
@limiter.limit("100/minute")
async def read_todo(
    request: Request, # limiter用
    todo_id: int,
    current_user: ActiveUserDep,
    todo_service: TodoServiceDep,
) -> Any:
    """
    指定されたIDのToDo項目を取得します。
    そのToDoが現在のユーザーのものである必要があります。
    """
    logger.debug("Fetching todo by id", todo_id=todo_id, user_id=current_user.id)
    try:
        todo = await todo_service.get_todo_by_id(todo_id=todo_id, owner_id=current_user.id)
        return todo
    except ResourceNotFoundException:
        logger.warning("Todo not found or access denied", todo_id=todo_id, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found")
    except AuthorizationException: # 念のため (get_todo_by_id内でチェックされる想定)
        logger.warning("Authorization denied for todo", todo_id=todo_id, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this ToDo")


# --- ToDo更新 ---
@router.put(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Update a ToDo item",
    description="Updates a specific ToDo item by its ID, if it belongs to the logged-in user.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "ToDo item not found or does not belong to the user"},
        status.HTTP_403_FORBIDDEN: {"description": "User not authorized to update this ToDo"},
    },
)
@limiter.limit("50/minute")
async def update_todo(
    request: Request, # limiter用
    todo_id: int,
    todo_in: TodoUpdate,
    current_user: ActiveUserDep,
    todo_service: TodoServiceDep,
) -> Any:
    """
    指定されたIDのToDo項目を更新します。
    そのToDoが現在のユーザーのものである必要があります。

    - **title**: 新しいタイトル (任意)
    - **description**: 新しい説明 (任意)
    - **is_completed**: 完了状態 (任意)
    """
    logger.info("Updating todo", todo_id=todo_id, user_id=current_user.id, data=todo_in.dict(exclude_unset=True))
    try:
        updated_todo = await todo_service.update_todo(
            todo_id=todo_id, todo_in=todo_in, owner_id=current_user.id
        )
        logger.info("Todo updated successfully", todo_id=todo_id, user_id=current_user.id)
        return updated_todo
    except ResourceNotFoundException:
        logger.warning("Todo not found for update", todo_id=todo_id, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found")
    except AuthorizationException: # 念のため
        logger.warning("Authorization denied for todo update", todo_id=todo_id, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this ToDo")

# --- ToDo削除 ---
@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a ToDo item",
    description="Deletes a specific ToDo item by its ID, if it belongs to the logged-in user.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "ToDo item not found or does not belong to the user"},
        status.HTTP_403_FORBIDDEN: {"description": "User not authorized to delete this ToDo"},
    },
)
@limiter.limit("50/minute")
async def delete_todo(
    request: Request, # limiter用
    todo_id: int,
    current_user: ActiveUserDep,
    todo_service: TodoServiceDep,
) -> None:
    """
    指定されたIDのToDo項目を削除します。
    そのToDoが現在のユーザーのものである必要があります。
    """
    logger.info("Deleting todo", todo_id=todo_id, user_id=current_user.id)
    try:
        await todo_service.delete_todo(todo_id=todo_id, owner_id=current_user.id)
        logger.info("Todo deleted successfully", todo_id=todo_id, user_id=current_user.id)
        # 204 No Content はレスポンスボディがないため、return None
        return None
    except ResourceNotFoundException:
        logger.warning("Todo not found for deletion", todo_id=todo_id, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found")
    except AuthorizationException: # 念のため
        logger.warning("Authorization denied for todo deletion", todo_id=todo_id, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this ToDo")

