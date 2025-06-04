# src/api/v1/endpoints/users.py
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter # Limiter をインポート

from libkoiki.schemas.user import UserCreate, UserUpdate, UserResponse
from libkoiki.services.user_service import UserService
from libkoiki.api.dependencies import (
    UserServiceDep,
    ActiveUserDep,
    SuperUserDep,
    DBSessionDep,
    has_permission,
)
# トランザクションデコレータを使用
from libkoiki.core.transaction import transactional
from libkoiki.core.exceptions import ValidationException, ResourceNotFoundException
from libkoiki.core.logging import get_logger
from libkoiki.core.rate_limiter import limiter

logger = get_logger(__name__)
router = APIRouter()

# --- ユーザー作成 ---
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user. By default, any user can create an account. Can be restricted (e.g., superuser only).",
    # dependencies=[Depends(RateLimitDep("5/minute"))] # ヘルパーを使用する場合
)
@transactional  # このデコレータがあるか確認
@limiter.limit("10/minute") # slowapi デコレータを使用
async def create_user(
    request: Request, # デコレータ使用時は Request が必要
    user_in: UserCreate,
    user_service: UserServiceDep,
    db: DBSessionDep, # トランザクショナルデコレータを使用するため必要
    # current_user: Optional[SuperUserDep] = None # 例: 管理者のみ作成可能にする場合。None許容にすると認証不要でも叩ける
) -> Any:
    """
    新規ユーザーを作成します。

    - **email**: ユーザーのメールアドレス (必須, ユニーク)
    - **password**: パスワード (必須, ポリシー準拠)
    - **full_name**: フルネーム (任意)
    """
    # if current_user is None: # 管理者のみ作成可能にする場合のチェック例
    #     logger.warning("Unauthorized attempt to create user")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can create users")

    logger.info("Attempting to create user", email=user_in.email)
    # サービス層でValidationExceptionが発生する可能性がある
    # グローバル例外ハンドラで処理される
    new_user = await user_service.create_user(user_in, db)
    logger.info("User created successfully", user_id=new_user.id, email=new_user.email)
    return new_user


# --- 自分の情報取得 ---
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information",
    description="Retrieves the profile information of the currently logged-in user."
)
async def read_user_me(
    current_user: ActiveUserDep, # 認証済みのアクティブユーザーを取得
    user_service: UserServiceDep,
    db: DBSessionDep
) -> Any:
    """現在のログインユーザー情報を取得します。"""
    logger.debug("Fetching current user info with roles", user_id=current_user.id)
    # 非同期リレーション参照エラー回避のため、ロールを含めて取得
    user = await user_service.get_user_with_roles(current_user.id, db)
    return user

# --- 自分の情報更新 ---
@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user information",
    description="Updates the profile information of the currently logged-in user.",
)
@limiter.limit("50/minute")
async def update_user_me(
    request: Request, # limiter用
    user_in: UserUpdate,
    current_user: ActiveUserDep,
    user_service: UserServiceDep,
    db: DBSessionDep # transactionalデコレータにはDBセッションが必要
) -> Any:
    """現在のログインユーザー情報を更新します。"""
    logger.info("Updating current user info", user_id=current_user.id, data=user_in.dict(exclude_unset=True))
    updated_user = await user_service.update_user(current_user.id, user_in, db)
    logger.info("Current user info updated successfully", user_id=current_user.id)
    
    # 非同期リレーション参照エラー回避のため、更新後にロールを含めて再取得
    user_with_roles = await user_service.get_user_with_roles(current_user.id, db)
    return user_with_roles

# --- ユーザー一覧取得 (管理者/特定権限持ち) ---
@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Get a list of users",
    description="Retrieves a list of users. Requires 'read:users' permission.",
    dependencies=[has_permission("read:users")] # RBACによる権限チェック
    # dependencies=[Depends(SuperUserDep)] # またはスーパーユーザーのみ
)
@limiter.limit("60/minute")
async def read_users(
    request: Request, # limiter用
    user_service: UserServiceDep,
    db: DBSessionDep, # データベース操作のため必要
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    ユーザー一覧を取得します (権限が必要)。

    - **skip**: スキップする件数
    - **limit**: 取得する最大件数
    """
    logger.debug("Fetching user list with roles", skip=skip, limit=limit)
    # 非同期リレーション参照エラーを回避するために、ロールを含めて取得するメソッドを使用
    users = await user_service.get_users_with_roles(skip=skip, limit=limit, db=db)
    logger.debug(f"Found {len(users)} users with roles preloaded")
    return users

# --- 権限ベースのエンドポイント例 ---
@router.get(
    "/protected-resource",
    summary="Example protected resource",
    description="Access requires 'read:protected_resource' permission.",
    dependencies=[has_permission("read:protected_resource")]
)
async def get_protected_resource(current_user: ActiveUserDep):
    """特定の権限を持つユーザーのみアクセス可能なリソース (サンプル)"""
    logger.debug("Access granted to protected resource", user_id=current_user.id)
    return {"message": f"Welcome {current_user.email}, you have the required permission ('read:protected_resource')!"}

# --- 特定ユーザー取得 (管理者/特定権限持ち) ---
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user by ID",
    description="Retrieves information for a specific user by their ID. Requires 'read:users' permission.",
    dependencies=[has_permission("read:users")],
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
@limiter.limit("100/minute")
async def read_user_by_id(
    request: Request, # limiter用
    user_id: int,
    user_service: UserServiceDep,
    db: DBSessionDep
) -> Any:
    """指定したIDのユーザー情報を取得します (権限が必要)。"""
    logger.debug("Fetching user with roles by ID", user_id=user_id)
    # 非同期リレーションエラー回避のため、ロールを含めて取得するメソッドを使用
    user = await user_service.get_user_with_roles(user_id, db)
    # get_user_by_idがNoneを返す場合（リポジトリの実装による）のエラーハンドリング
    if user is None:
        logger.warning("User not found by ID", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    return user

# --- 特定ユーザー更新 (管理者/特定権限持ち) ---
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user by ID",
    description="Updates information for a specific user by their ID. Requires 'update:users' permission.",
    dependencies=[has_permission("update:users")],
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
@limiter.limit("50/minute")
async def update_user_by_id(
    request: Request, # limiter用
    user_id: int,
    user_in: UserUpdate,
    user_service: UserServiceDep,
    db: DBSessionDep, # transactionalデコレータが必要
    current_admin: ActiveUserDep, # 操作者情報をログ等で使用する場合
) -> Any:
    """指定したIDのユーザー情報を更新します (権限が必要)。"""
    logger.info("Updating user by ID", target_user_id=user_id, admin_user_id=current_admin.id, data=user_in.dict(exclude_unset=True))
    # is_superuser の変更など、特別な権限チェックが必要な場合がある
    if 'is_superuser' in user_in.dict(exclude_unset=True) and not current_admin.is_superuser:
        logger.warning("Non-superuser attempting to change superuser status", admin_user_id=current_admin.id, target_user_id=user_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only superusers can change superuser status")

    try:
        updated_user = await user_service.update_user(user_id, user_in, db)
        logger.info("User updated successfully by admin", target_user_id=user_id, admin_user_id=current_admin.id)
        return updated_user
    except ResourceNotFoundException:
        logger.warning("User not found for update by admin", target_user_id=user_id, admin_user_id=current_admin.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
    except ValidationException as e: # パスワードポリシー違反など
        logger.warning("Validation failed during user update by admin", target_user_id=user_id, admin_user_id=current_admin.id, error=str(e.detail))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)

# --- 特定ユーザー削除 (管理者/特定権限持ち) ---
@router.delete(
    "/{user_id}",
    response_model=UserResponse, # 削除されたユーザー情報を返す（または status_code=204）
    # status_code=status.HTTP_204_NO_CONTENT, # ボディを返さない場合
    summary="Delete a user by ID",
    description="Deletes a specific user by their ID. Requires 'delete:users' permission.",
    dependencies=[has_permission("delete:users")],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Cannot delete own account"}
    },
)
@limiter.limit("30/minute")
async def delete_user_by_id(
    request: Request, # limiter用
    user_id: int,
    current_admin: ActiveUserDep, # ActiveUserDepでも良いが、権限チェック済み
    user_service: UserServiceDep,
    db: DBSessionDep # transactionalデコレータが必要
) -> Any:
    """指定したIDのユーザーを削除します (権限が必要)。"""
    logger.info("Deleting user by ID", target_user_id=user_id, admin_user_id=current_admin.id)
    if user_id == current_admin.id:
        logger.warning("Admin attempted to delete own account", user_id=current_admin.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete own account")
    # サービス層でResourceNotFoundExceptionが発生する可能性がある
    try:
        deleted_user = await user_service.delete_user(user_id, db)
        # delete_userがNoneを返す場合のエラーハンドリングは不要（例外を投げる実装のため）
        logger.info("User deleted successfully by admin", target_user_id=user_id, admin_user_id=current_admin.id)
        return deleted_user # 削除されたユーザー情報を返す
        # return None # 204 No Content の場合
    except ResourceNotFoundException:
        logger.warning("User not found for deletion by admin", target_user_id=user_id, admin_user_id=current_admin.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")
