"""
KOIKI-FW セキュリティデータ初期化スクリプト
権限・ロール・テストユーザーの一括セットアップ
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.core.security import get_password_hash
from libkoiki.db.session import get_db, init_db_engine
from libkoiki.models.permission import PermissionModel
from libkoiki.models.role import RoleModel
from libkoiki.models.user import UserModel
from libkoiki.repositories.user_repository import UserRepository

# 権限・ロール定義のインポート
from ops.security.roles_permissions import (
    BASIC_PERMISSIONS,
    BASIC_ROLES,
    INITIAL_USER_ROLES,
    TEST_USERS,
)


async def setup_permissions(session: AsyncSession) -> dict:
    """基本権限の作成"""
    print("🔑 権限の設定を開始...")
    permissions = {}

    for perm_key, perm_data in BASIC_PERMISSIONS.items():
        # 既存権限の確認
        result = await session.execute(
            select(PermissionModel).where(PermissionModel.name == perm_data["name"])
        )
        existing_perm = result.scalar_one_or_none()

        if not existing_perm:
            permission = PermissionModel(
                name=perm_data["name"], description=perm_data["description"]
            )
            session.add(permission)
            await session.flush()
            permissions[perm_key] = permission
            print(f"  ✅ 権限作成: {perm_data['name']}")
        else:
            permissions[perm_key] = existing_perm
            print(f"  ℹ️  権限存在: {perm_data['name']}")

    return permissions


async def setup_roles(session: AsyncSession, permissions: dict) -> dict:
    """基本ロールの作成"""
    print("\n👥 ロールの設定を開始...")
    roles = {}

    for role_key, role_data in BASIC_ROLES.items():
        # 既存ロールの確認
        result = await session.execute(
            select(RoleModel).where(RoleModel.name == role_data["name"])
        )
        existing_role = result.scalar_one_or_none()

        if not existing_role:
            role = RoleModel(
                name=role_data["name"], description=role_data["description"]
            )

            # 権限の割り当て
            for perm_name in role_data["permissions"]:
                # 権限名からキーを検索
                perm_key = None
                for key, perm in permissions.items():
                    if perm.name == perm_name:
                        perm_key = key
                        break

                if perm_key and perm_key in permissions:
                    role.permissions.append(permissions[perm_key])

            session.add(role)
            await session.flush()
            roles[role_key] = role
            print(
                f"  ✅ ロール作成: {role_data['name']} (権限: {len(role_data['permissions'])}個)"
            )
        else:
            roles[role_key] = existing_role
            print(f"  ℹ️  ロール存在: {role_data['name']}")

    return roles


async def cleanup_existing_test_users(session: AsyncSession):
    """既存のテストユーザーを削除（開発用データの整理）"""
    print("\n🧹 既存テストユーザーのクリーンアップ...")

    test_emails = [user["email"] for user in TEST_USERS]
    test_usernames = [user["username"] for user in TEST_USERS]

    # テスト用ユーザーの削除
    for email in test_emails:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            # 関連データが自動削除されるようにDelete処理を実行
            await session.delete(user)
            print(f"  🗑️  削除: {email}")

    # ユーザー名でも確認して削除
    for username in test_usernames:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            await session.delete(user)
            print(f"  🗑️  削除: {username}")


async def setup_test_users(session: AsyncSession):
    """テストユーザーの作成（クリーンな状態から）"""
    print("\n👤 テストユーザーの設定を開始...")

    # 既存テストデータのクリーンアップ
    await cleanup_existing_test_users(session)
    await session.flush()  # 削除を反映

    user_repo = UserRepository()
    user_repo.set_session(session)

    for user_data in TEST_USERS:
        # パスワードハッシュ化
        hashed_password = get_password_hash(user_data["password"])

        # ユーザー作成
        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            is_superuser=user_data["is_superuser"],
            is_active=user_data["is_active"],
        )

        session.add(user)
        await session.flush()
        print(f"  ✅ ユーザー作成: {user_data['email']} ({user_data['username']})")

        # ロールの割り当て
        if user_data["email"] in INITIAL_USER_ROLES:
            role_names = INITIAL_USER_ROLES[user_data["email"]]
            for role_name in role_names:
                # ロールを検索
                stmt = select(RoleModel).where(RoleModel.name == role_name)
                result = await session.execute(stmt)
                role = result.unique().scalar_one_or_none()

                if role:
                    # 直接的にユーザーロール関連テーブルに挿入
                    from sqlalchemy import insert

                    from libkoiki.models.associations import user_roles

                    # user_roles 関連テーブルに挿入
                    stmt = insert(user_roles).values(user_id=user.id, role_id=role.id)
                    await session.execute(stmt)
                    print(f"  ✅ ロール割り当て: {user_data['email']} -> {role_name}")
                else:
                    print(f"  ⚠️  ロール未発見: {role_name}")


async def setup_security_data():
    """セキュリティデータの一括セットアップ"""
    print("🔐 KOIKI-FW セキュリティデータセットアップ開始")
    print("=" * 60)

    # データベース初期化
    init_db_engine()

    async for session in get_db():
        try:
            # 1. 権限の作成
            permissions = await setup_permissions(session)

            # 2. ロールの作成
            roles = await setup_roles(session, permissions)

            # 3. テストユーザーの作成（ロール割り当て含む）
            await setup_test_users(session)

            # 4. コミット
            await session.commit()

            print("\n" + "=" * 60)
            print("✅ セキュリティデータのセットアップが完了しました！")

            # 作成内容の要約
            print(f"\n📋 作成された内容:")
            print(f"  • 権限: {len(BASIC_PERMISSIONS)}個")
            print(f"  • ロール: {len(BASIC_ROLES)}個")
            print(f"  • テストユーザー: {len(TEST_USERS)}個")

            print(f"\n🔑 テスト用ログイン情報:")
            for user in TEST_USERS:
                roles = INITIAL_USER_ROLES.get(user["email"], ["なし"])
                print(
                    f"  • {user['email']} / {user['password']} (ロール: {', '.join(roles)})"
                )

            break

        except Exception as e:
            await session.rollback()
            print(f"❌ セットアップエラー: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(setup_security_data())
