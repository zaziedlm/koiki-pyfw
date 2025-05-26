# src/api/dependencies.py
from typing import Optional, Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # Eager loading用
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from libkoiki.db.session import get_db as get_db_session
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.repositories.todo_repository import TodoRepository # ★ToDoリポジトリ追加★
from libkoiki.services.user_service import UserService
from libkoiki.services.todo_service import TodoService # ★ToDoサービス追加★
from libkoiki.events.publisher import EventPublisher
from libkoiki.core.security import get_user_from_token as get_current_user_from_token # 名前変更
from libkoiki.models.user import UserModel
from libkoiki.models.role import RoleModel # ★RoleModelインポート★
from libkoiki.core.config import settings
from libkoiki.core.logging import get_logger

logger = get_logger(__name__)

# --- 基本的な依存性 ---
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# --- Redis クライアント (アプリケーション状態から取得) ---
async def get_redis_client(request: Request) -> Redis:
    """アプリケーション状態からRedisクライアントを取得"""
    if not hasattr(request.app.state, 'redis') or not request.app.state.redis:
        logger.error("Redis client requested but not available in app state.")
        raise HTTPException(status_code=503, detail="Redis connection not available")
    return request.app.state.redis

RedisClientDep = Annotated[Redis, Depends(get_redis_client)]

# --- イベントパブリッシャー (アプリケーション状態から取得) ---
async def get_event_publisher(request: Request) -> Optional[EventPublisher]:
    """アプリケーション状態からイベントパブリッシャーを取得"""
    # 起動時に設定されていれば返す、なければNone
    publisher = getattr(request.app.state, 'event_publisher', None)
    # if publisher is None:
        # logger.warning("Event publisher requested but not available in app state.")
    return publisher

EventPublisherDep = Annotated[Optional[EventPublisher], Depends(get_event_publisher)]

# --- レートリミッター (アプリケーション状態から取得) ---
async def get_limiter(request: Request) -> Limiter:
    """アプリケーション状態からレートリミッターを取得"""
    if not hasattr(request.app.state, 'limiter') or not request.app.state.limiter:
         logger.error("Rate limiter requested but not configured in application state.")
         raise RuntimeError("Rate limiter not configured in application state")
    return request.app.state.limiter

LimiterDep = Annotated[Limiter, Depends(get_limiter)]

# エンドポイントで @Depends(RateLimitDep()) や @Depends(RateLimitDep("5/minute")) のように使うためのヘルパー
# Depends(...) を返す関数として定義
def RateLimitDep(limit_str: Optional[str] = None):
    """
    エンドポイント固有のレートリミットを適用するための依存性。
    limiterインスタンス自体を取得する場合は LimiterDep を使用。
    """
    async def dependency(request: Request, limiter: LimiterDep):
        if not limiter.enabled:
            return # レートリミット無効なら何もしない

        key = limiter.key_func(request)
        # リミット文字列が指定されていればそれを使用、なければデフォルト
        effective_limit_str = limit_str or settings.RATE_LIMIT_DEFAULT
        try:
            # 文字列からRateLimitItemをパース
            limit, granularity = effective_limit_str.split('/')
            limit = int(limit)
            # シンプルな時間単位のパース (例: minute, hour, day)
            # slowapi内部のパースロジックを利用するのがより堅牢
            if granularity == "minute": seconds = 60
            elif granularity == "hour": seconds = 3600
            elif granularity == "day": seconds = 86400
            else: seconds = 1 # 不明な場合は秒単位? 要検討

            # NOTE: slowapiの内部実装に依存する可能性があるため、
            #       `limiter.check` や `limiter.hit` を直接使う方が安定するかも。
            #       しかし、それらは通常デコレータ内で使われる。
            #       ここでは簡易的なチェック処理のイメージを示す。
            #
            # 代替案: slowapiの `limiter.limit` デコレータ相当の処理をここで行う
            # current_limit = RateLimitItem(limit, seconds) # 仮のRateLimitItem
            # if not await limiter.hit(current_limit, key):
            #     raise RateLimitExceeded(effective_limit_str)
            #
            # 現状のSlowAPIでは、Depends内で直接制限チェックを行う標準的な方法は提供されていない。
            # エンドポイントデコレータ `@limiter.limit("...")` を使うのが最も簡単。
            # ここでは依存性としてLimiterインスタンスを提供する役割に留める。
            # logger.debug(f"Applying rate limit check: {effective_limit_str} for key {key}")
            pass # 実際のチェックはエンドポイントデコレータかミドルウェアが行う想定
        except ValueError:
            logger.error(f"Invalid rate limit string: {effective_limit_str}")
            raise HTTPException(status_code=500, detail="Invalid rate limit configuration")
        return limiter # Limiterインスタンスを返す（チェック自体はしない）
    return Depends(dependency)


# --- リポジトリ ---
# リポジトリはサービス層内部でインスタンス化される方がシンプル
# (サービスがトランザクションスコープでリポジトリにセッションを渡すため)

# --- サービス ---
# サービスはリクエストごとにインスタンス化
def get_user_service(event_publisher: EventPublisherDep) -> UserService:
    """UserServiceインスタンスを生成"""
    user_repo = UserRepository() # サービス内でリポジトリをインスタンス化
    return UserService(repository=user_repo, event_publisher=event_publisher)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# ★ ToDo サービス依存性 ★
def get_todo_service() -> TodoService:
    """TodoServiceインスタンスを生成"""
    todo_repo = TodoRepository()
    return TodoService(repository=todo_repo)

TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]

# --- 認証・認可 ---
# get_current_user_from_token はトークン検証とDBアクセスを行う
CurrentUserDep = Annotated[UserModel, Depends(get_current_user_from_token)]

# アクティブユーザーチェック
async def get_current_active_user(
    user_id: CurrentUserDep,
    db: DBSessionDep
):
    """現在認証されているアクティブなユーザーを取得"""
    if not user_id: # get_current_user_from_tokenがNoneを返す場合（エラー処理はそちらで行われる想定）
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # ユーザーIDからユーザーオブジェクトを取得
    user_repo = UserRepository()
    user_repo.set_session(db)
    current_user = await user_repo.get_user_with_roles_permissions(user_id)
    
    if not current_user:
        logger.warning("User not found in DB", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    if not current_user.is_active:
        logger.warning("Attempt to access by inactive user", user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    return current_user

ActiveUserDep = Annotated[UserModel, Depends(get_current_active_user)]

# スーパーユーザーチェック
def get_current_active_superuser(current_user: ActiveUserDep):
    """現在認証されているアクティブなスーパーユーザーを取得"""
    if not current_user.is_superuser:
        logger.warning("Superuser access denied for user", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

SuperUserDep = Annotated[UserModel, Depends(get_current_active_superuser)]

# 権限チェック (RBAC)
def has_permission(required_permission: str):
    """指定された権限を持つかをチェックする依存性ファクトリ"""
    async def dependency(
        current_user: ActiveUserDep,
        db: DBSessionDep # ロール/権限の遅延ロード用
    ):
        # UserModelにrolesとpermissionsが適切にロードされているか確認
        # get_current_user_from_token で selectinload を使っている前提
        # もしロードされていない場合は、ここで明示的にロードする (パフォーマンスに影響あり)
        if not hasattr(current_user, 'roles') or not current_user.roles:
             # ロール情報がロードされていない場合、DBから再取得またはロード
             logger.debug("Roles not preloaded for user, loading now...", user_id=current_user.id)
             user_repo = UserRepository()
             user_repo.set_session(db)
             # ロールと権限を eager load するメソッドをリポジトリに用意する
             loaded_user = await user_repo.get_user_with_roles_permissions(current_user.id)
             if not loaded_user: # ユーザーが見つからない場合 (通常は発生しないはず)
                 raise HTTPException(status_code=404, detail="User not found during permission check")
             current_user = loaded_user # ロードされたユーザー情報で上書き

        if not hasattr(current_user, 'roles'):
             logger.error("User role information still not available after loading attempt.", user_id=current_user.id)
             raise HTTPException(status_code=500, detail="User role information not loaded")

        # スーパーユーザーは常に全ての権限を持つ
        if current_user.is_superuser:
            return None  # 権限チェックをパス
        
        user_permissions = set()
        for role in current_user.roles:
            # Role に permissions がロードされているか確認 (get_user_with_roles_permissionsでロードされる想定)
            if hasattr(role, 'permissions') and role.permissions:
                 for perm in role.permissions:
                     user_permissions.add(perm.name)
            else:
                 # Roleに紐づくPermissionがない、またはロードされていない場合のログ
                 logger.debug(f"Role '{role.name}' has no permissions or permissions not loaded.", role_id=role.id)


        if required_permission not in user_permissions:
            logger.warning(
                "Permission denied for user",
                user_id=current_user.id,
                required_permission=required_permission,
                user_permissions=list(user_permissions) # setはJSON不可なのでリスト化
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        logger.debug("Permission granted", user_id=current_user.id, permission=required_permission)
        return current_user # 権限チェックOKならユーザーを返す
    return Depends(dependency) # Depends() でラップして返す
