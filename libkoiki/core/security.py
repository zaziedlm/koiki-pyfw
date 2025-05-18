# src/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, Annotated # Annotated をインポート
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from libkoiki.core.config import settings
from libkoiki.schemas.token import TokenPayload
from libkoiki.repositories.user_repository import UserRepository # リポジトリ使用
# from libkoiki.db.session import get_db as get_db_session # 循環参照を避けるため、ここでは直接呼ばない
from libkoiki.models.user import UserModel
from libkoiki.models.role import RoleModel # RoleModelをインポート
from libkoiki.models.permission import PermissionModel # PermissionModelをインポート
import structlog

logger = structlog.get_logger(__name__)

# --- パスワードハッシュ化 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 スキーマ ---
# tokenUrl は認証エンドポイントの相対パス
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

# --- トークン生成 ---
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    新しいアクセストークンを生成します。

    Args:
        subject: トークンの主体 (通常はユーザーID)。
        expires_delta: トークンの有効期間。None の場合は設定値を使用。

    Returns:
        生成されたJWTトークン文字列。
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)} # subject は文字列に変換
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug("Access token created", subject=subject, expires_at=expire.isoformat())
    return encoded_jwt

# --- パスワード検証 ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化されたパスワードを比較検証します"""
    return pwd_context.verify(plain_password, hashed_password)

# --- パスワードハッシュ化 ---
def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化します"""
    return pwd_context.hash(password)

# --- トークンからユーザーを取得 (依存性注入用) ---
async def get_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    # DBセッションは依存性注入で取得 (循環参照を避ける)
    # db: Annotated[AsyncSession, Depends(get_db_session)] # main.py で get_db_session を定義
    # -> 代わりに、dependencies.pyで get_db_session を使う
    # -> ここでは Session を直接引数に取らないように変更
) -> Optional[UserModel]:
    """
    JWTトークンを検証し、対応するユーザー情報をDBから取得します。
    ロールと権限も Eager Loading します。
    DBセッションは呼び出し元 (e.g., dependencies.py) で提供される必要があります。

    Args:
        token: Authorizationヘッダーから抽出されたJWTトークン。

    Returns:
        ユーザーモデルオブジェクト、または無効なトークンの場合は None。
        実際には無効な場合は HTTPException を送出する。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload) # ペイロードをスキーマで検証
        # 有効期限チェック
        if token_data.exp is None or datetime.fromtimestamp(token_data.exp, timezone.utc) < datetime.now(timezone.utc):
             logger.warning("Token expired", user_id=token_data.sub, exp=token_data.exp)
             raise credentials_exception
        # サブジェクト (ユーザーID) チェック
        if token_data.sub is None:
            logger.warning("Token subject (user ID) is missing")
            raise credentials_exception
        user_id = int(token_data.sub) # IDを整数に変換
        logger.debug("Token decoded successfully", user_id=user_id)

    except (JWTError, ValidationError) as e:
        logger.warning(f"Token validation failed: {e}", token=token[:10]+"...") # トークンの一部だけログに
        raise credentials_exception

    # DBセッションを取得 (ここでは取得せず、依存性として渡される想定)
    # この関数を使う dependencies.py の中で db セッションを取得する
    # logger.debug("Attempting to fetch user from DB", user_id=user_id)
    # user_repo = UserRepository()
    # user_repo.set_session(db) # 渡された db セッションを使用
    # # 権限チェックのために roles と permissions を Eager Loading する
    # user = await user_repo.get_user_with_roles_permissions(user_id)

    # if user is None:
    #     logger.warning("User specified in token not found in DB", user_id=user_id)
    #     raise credentials_exception
    # logger.debug("User fetched from DB successfully", user_id=user_id)
    # return user

    # DB アクセスはこの関数から分離し、依存性関数内で処理する
    # この関数はトークン検証とユーザーIDの抽出のみを担当
    return user_id # ユーザーIDを返す


# --- 現在のユーザーを取得する依存性関数 (dependencies.pyで使用) ---
# この関数は get_user_from_token と DB セッションに依存する
# async def get_current_user(
#     user_id: Annotated[int, Depends(get_user_from_token)],
#     db: Annotated[AsyncSession, Depends(get_db_session)] # ここでDBセッションを取得
# ) -> Optional[UserModel]:
#     if user_id is None: # get_user_from_token が ID を返さない場合 (エラーはそちらで発生)
#         return None
#
#     logger.debug("Fetching user from DB for get_current_user", user_id=user_id)
#     user_repo = UserRepository()
#     user_repo.set_session(db) # 渡された db セッションを使用
#     user = await user_repo.get_user_with_roles_permissions(user_id)
#
#     if user is None:
#         logger.error("User specified in token not found in DB during get_current_user", user_id=user_id)
#         # get_user_from_token でチェックされるはずだが念のため
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials (user not found)",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     logger.debug("User fetched for get_current_user successfully", user_id=user_id)
#     return user

# --- パスワードポリシーヘルパー ---
import re

def check_password_complexity(password: str) -> bool:
    """
    簡単なパスワード複雑性チェック。
    - 8文字以上
    - 少なくとも1つの小文字を含む ([a-z])
    - 少なくとも1つの大文字を含む ([A-Z])
    - 少なくとも1つの数字を含む ([0-9])
    - 少なくとも1つの記号を含む (例: !@#$%^&*(),.?":{}|<>)
    """
    if len(password) < 8:
        logger.debug("Password complexity check failed: too short")
        return False
    if not re.search(r"[a-z]", password):
        logger.debug("Password complexity check failed: no lowercase letter")
        return False
    if not re.search(r"[A-Z]", password):
        logger.debug("Password complexity check failed: no uppercase letter")
        return False
    if not re.search(r"\d", password):
        logger.debug("Password complexity check failed: no digit")
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): # 記号の種類は要件に合わせて調整
        logger.debug("Password complexity check failed: no symbol")
        return False
    logger.debug("Password complexity check passed")
    return True

# --- UserRepository に get_user_with_roles_permissions を追加する必要がある ---
# (user_repository.py に実装済み)
