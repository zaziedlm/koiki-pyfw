# src/services/user_service.py
from typing import Optional, Sequence  # 必要な型のみをインポート

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from libkoiki.core.exceptions import ResourceNotFoundException, ValidationException
from libkoiki.core.monitoring import increment_user_registration  # カスタムメトリクス
from libkoiki.core.security import (
    check_password_complexity,
    get_password_hash,
    verify_password,
)
from libkoiki.core.transaction import transactional  # トランザクションデコレータ
from libkoiki.events.publisher import EventPublisher
from libkoiki.models.user import UserModel
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.schemas.user import UserCreate, UserUpdate

logger = structlog.get_logger(__name__)


class UserService:
    """ユーザー関連のビジネスロジックを処理するサービスクラス"""

    def __init__(
        self,
        repository: UserRepository,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.repository = repository
        self.event_publisher = event_publisher

    async def get_user_by_id(
        self, user_id: int, db: AsyncSession
    ) -> Optional[UserModel]:  # Optionalを返すように修正
        """IDでユーザーを取得します"""
        logger.debug("Service: Getting user by ID", user_id=user_id)
        self.repository.set_session(db)
        user = await self.repository.get(user_id)
        if not user:
            logger.info("Service: User not found by ID", user_id=user_id)
            # サービス層ではNoneを返し、API層で404にする方が柔軟な場合もある
            # raise ResourceNotFoundException(resource_name="User", resource_id=user_id)
            return None
        return user

    async def get_user_by_email(
        self, email: str, db: AsyncSession
    ) -> Optional[UserModel]:
        """Emailでユーザーを取得します"""
        logger.debug("Service: Getting user by email", email=email)
        self.repository.set_session(db)
        return await self.repository.get_by_email(email)

    async def get_users(
        self, skip: int, limit: int, db: AsyncSession
    ) -> Sequence[UserModel]:
        """ユーザーリストを取得します"""
        logger.debug("Service: Getting user list", skip=skip, limit=limit)
        self.repository.set_session(db)
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def get_user_with_roles(
        self, user_id: int, db: AsyncSession
    ) -> Optional[UserModel]:
        """IDでユーザーをロール情報も含めて取得します"""
        logger.debug("Service: Getting user with roles by ID", user_id=user_id)
        self.repository.set_session(db)

        # selectinloadを使用してロールを一度に取得
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == user_id)
        )

        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.info("Service: User not found by ID", user_id=user_id)
            return None

        return user

    async def get_users_with_roles(
        self, skip: int, limit: int, db: AsyncSession
    ) -> Sequence[UserModel]:
        """ユーザーリストをロール情報も含めて取得します"""
        logger.debug("Service: Getting user list with roles", skip=skip, limit=limit)
        self.repository.set_session(db)

        # selectinloadを使用してロールを一度に取得
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    @transactional
    async def create_user(self, user_in: UserCreate, db: AsyncSession) -> UserModel:
        """
        新規ユーザーを作成します。
        トランザクション内でメールアドレスの重複チェックとユーザー作成を行います。
        """
        logger.info("Service: Creating user", email=user_in.email)
        self.repository.set_session(db)

        # メールアドレスの重複チェック
        existing_user = await self.repository.get_by_email(user_in.email)
        if existing_user:
            logger.warning("Service: Email already exists", email=user_in.email)
            raise ValidationException("This email address is already registered.")

        # パスワードポリシーチェック
        if not check_password_complexity(user_in.password):
            logger.warning(
                "Service: Password does not meet complexity requirements",
                email=user_in.email,
            )
            raise ValidationException(
                "Password does not meet complexity requirements. It must be at least 8 characters long and include uppercase, lowercase, digit, and symbol."
            )

        # パスワードをハッシュ化
        hashed_password = get_password_hash(user_in.password)

        # ORMモデルインスタンスを作成
        user_data = user_in.dict(
            exclude={"password"}
        )  # スキーマから辞書へ (パスワード除外)
        user_data["hashed_password"] = hashed_password
        # is_active, is_superuser はスキーマのデフォルト値が使われる (UserCreateに定義があれば)
        # もしなければここで明示的に設定: user_data["is_active"] = True, user_data["is_superuser"] = False
        new_user = UserModel(**user_data)  # リポジトリで作成
        created_user = await self.repository.create(new_user)
        logger.info(
            "Service: User created successfully",
            user_id=created_user.id,
            email=created_user.email,
        )

        # カスタムメトリクスをインクリメント
        increment_user_registration()

        # イベント発行 (非同期的が良い場合が多い)
        if self.event_publisher:
            try:
                await self.event_publisher.publish(
                    "user_created",
                    {"user_id": created_user.id, "email": created_user.email},
                )
            except Exception:
                # イベント発行失敗はログに残すが、ユーザー作成自体は成功とする
                logger.error(
                    "Failed to publish user_created event",
                    user_id=created_user.id,
                    exc_info=True,
                )

        # 明示的にロールをロードして返す（非同期リレーション参照エラー回避）
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == created_user.id)
        )

        result = await db.execute(stmt)
        user_with_roles = result.scalar_one_or_none()
        if user_with_roles:
            return user_with_roles

        # 万が一ロードに失敗した場合は作成したユーザーをそのまま返す
        return created_user

    @transactional
    async def update_user(
        self, user_id: int, user_in: UserUpdate, db: AsyncSession
    ) -> UserModel:
        """ユーザー情報を更新します。"""
        logger.info(
            "Service: Updating user",
            user_id=user_id,
            data=user_in.dict(exclude_unset=True),
        )
        self.repository.set_session(db)

        # 更新対象のユーザーを取得
        user = await self.repository.get(user_id)
        if not user:
            logger.warning("Service: User not found for update", user_id=user_id)
            raise ResourceNotFoundException(resource_name="User", resource_id=user_id)

        # 更新データを用意 (Pydanticスキーマから exclude_unset=True で)
        update_data = user_in.dict(exclude_unset=True)

        # パスワード更新がある場合
        if "password" in update_data and update_data["password"]:
            # パスワードポリシーチェック
            if not check_password_complexity(update_data["password"]):
                logger.warning(
                    "Service: New password does not meet complexity requirements",
                    user_id=user_id,
                )
                raise ValidationException(
                    "Password does not meet complexity requirements."
                )
            # 新しいパスワードをハッシュ化して設定
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]  # 平文パスワードは削除
        elif "password" in update_data:  # passwordキーはあるが値が空やNoneの場合
            del update_data["password"]  # 更新しない

        # メールアドレス変更時の重複チェック (変更がある場合のみ)
        if "email" in update_data and update_data["email"] != user.email:
            logger.debug(
                "Service: Checking for email duplication on update",
                new_email=update_data["email"],
            )
            existing_user = await self.repository.get_by_email(update_data["email"])
            if existing_user and existing_user.id != user_id:
                logger.warning(
                    "Service: Email already exists during update",
                    new_email=update_data["email"],
                )
                raise ValidationException(
                    "This email address is already registered by another user."
                )

        # is_superuser の更新は特別な権限が必要かもしれない (API層でチェック済み想定)
        # if 'is_superuser' in update_data and not calling_user.is_superuser:
        #     raise AuthorizationException(...)        # リポジトリで更新
        updated_user = await self.repository.update(user, update_data)
        logger.info("Service: User updated successfully", user_id=user_id)

        # イベント発行
        if self.event_publisher:
            try:
                await self.event_publisher.publish(
                    "user_updated", {"user_id": updated_user.id}
                )
            except Exception:
                logger.error(
                    "Failed to publish user_updated event",
                    user_id=updated_user.id,
                    exc_info=True,
                )

        # 非同期リレーション参照エラー回避のため、明示的にロールを取得
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == updated_user.id)
        )

        result = await db.execute(stmt)
        user_with_roles = result.scalar_one_or_none()
        if user_with_roles:
            return user_with_roles

        # 万が一ロードに失敗した場合は更新したユーザーをそのまま返す

        return updated_user

    async def authenticate_user(
        self, email: str, password: str, db: Optional[AsyncSession] = None
    ) -> Optional[UserModel]:
        """
        ユーザーを認証します。
        成功した場合はユーザーモデルを、失敗した場合は None を返します。
        """
        logger.debug("Service: Authenticating user", email=email)
        # DBセッションが渡された場合は設定
        if db is not None:
            self.repository.set_session(db)
        user = await self.repository.get_by_email(email)
        if not user:
            logger.info("Authentication failed: User not found", email=email)
            return None
        if not verify_password(password, user.hashed_password):
            logger.info(
                "Authentication failed: Incorrect password",
                email=email,
                user_id=user.id,
            )
            # TODO: ログイン失敗回数を記録・ロックアウトする機能を追加検討
            return None
        # 認証成功
        logger.info("Authentication successful", email=email, user_id=user.id)
        # TODO: 最終ログイン日時を更新する処理を追加検討
        return user

    @transactional
    async def delete_user(self, user_id: int, db: AsyncSession) -> Optional[UserModel]:
        """ユーザーを削除します"""
        logger.info("Service: Deleting user", user_id=user_id)
        self.repository.set_session(db)
        deleted_user = await self.repository.delete(user_id)
        if deleted_user is None:
            logger.warning("Service: User not found for deletion", user_id=user_id)
            raise ResourceNotFoundException(resource_name="User", resource_id=user_id)

        logger.info("Service: User deleted successfully", user_id=user_id)
        # イベント発行
        if self.event_publisher:
            try:
                # 削除されたユーザーの情報が必要な場合があるため、オブジェクトを渡す
                await self.event_publisher.publish(
                    "user_deleted",
                    {"user_id": deleted_user.id, "email": deleted_user.email},
                )
            except Exception:
                logger.error(
                    "Failed to publish user_deleted event",
                    user_id=deleted_user.id,
                    exc_info=True,
                )

        return deleted_user

    # --- ロール・権限関連メソッド (必要に応じて) ---
    # @transactional
    # async def assign_role_to_user(self, user_id: int, role_name: str, db: AsyncSession): ...
    # @transactional
    # async def remove_role_from_user(self, user_id: int, role_name: str, db: AsyncSession): ...
    # async def get_user_permissions(self, user_id: int, db: AsyncSession) -> List[str]: ...
