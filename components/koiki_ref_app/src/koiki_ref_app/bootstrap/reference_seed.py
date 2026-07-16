"""Idempotent reference-application bootstrap data.

This module owns only reference-app data that is safe outside development:
roles, permissions, their associations, and the business-clock singleton.
It intentionally never creates a user or a password.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from koiki_ref_app.bootstrap.orm import bootstrap_orm
from koiki_ref_app.models.kkbiz import BusinessClock
from libkoiki.db.session import dispose_db_engine, get_db, init_db_engine
from libkoiki.models.associations import role_permissions
from libkoiki.models.permission import PermissionModel
from libkoiki.models.role import RoleModel


REFERENCE_PERMISSIONS = {
    "read:security_metrics": {
        "name": "read:security_metrics",
        "description": "セキュリティメトリクスの参照",
        "resource": "security",
        "action": "read",
    },
    "manage:security_metrics": {
        "name": "manage:security_metrics",
        "description": "セキュリティメトリクスの管理・リセット",
        "resource": "security",
        "action": "manage",
    },
    "read:users": {
        "name": "read:users",
        "description": "ユーザー情報の参照",
        "resource": "users",
        "action": "read",
    },
    "write:users": {
        "name": "write:users",
        "description": "ユーザー情報の編集・作成・削除",
        "resource": "users",
        "action": "write",
    },
    "read:todos": {
        "name": "read:todos",
        "description": "ToDo項目の参照",
        "resource": "todos",
        "action": "read",
    },
    "write:todos": {
        "name": "write:todos",
        "description": "ToDo項目の編集・作成・削除",
        "resource": "todos",
        "action": "write",
    },
    "admin:system": {
        "name": "admin:system",
        "description": "システム全体の管理者権限",
        "resource": "system",
        "action": "admin",
    },
}

REFERENCE_ROLES = {
    "security_admin": {
        "name": "security_admin",
        "description": "セキュリティ管理者",
        "permissions": [
            "read:security_metrics",
            "manage:security_metrics",
            "read:users",
        ],
    },
    "user_admin": {
        "name": "user_admin",
        "description": "ユーザー管理者",
        "permissions": ["read:users", "write:users", "read:todos"],
    },
    "todo_user": {
        "name": "todo_user",
        "description": "一般ユーザー（ToDo操作のみ）",
        "permissions": ["read:todos", "write:todos"],
    },
    "system_admin": {
        "name": "system_admin",
        "description": "システム管理者（全権限）",
        "permissions": list(REFERENCE_PERMISSIONS),
    },
}


@dataclass(frozen=True)
class ReferenceSeedResult:
    permissions_created: int
    roles_created: int
    role_permissions_created: int
    business_clock_created: bool


async def seed_reference_data(session: AsyncSession) -> ReferenceSeedResult:
    """Insert or reconcile reference-owned seed data without creating users."""
    bootstrap_orm()
    permissions: dict[str, PermissionModel] = {}
    permissions_created = 0
    roles_created = 0
    role_permissions_created = 0

    for key, values in REFERENCE_PERMISSIONS.items():
        permission = await session.scalar(
            select(PermissionModel).where(PermissionModel.name == values["name"])
        )
        if permission is None:
            permission = PermissionModel(**values)
            session.add(permission)
            permissions_created += 1
        else:
            permission.description = values["description"]
            permission.resource = values["resource"]
            permission.action = values["action"]
        permissions[key] = permission

    await session.flush()

    for role_data in REFERENCE_ROLES.values():
        role = await session.scalar(
            select(RoleModel).where(RoleModel.name == role_data["name"])
        )
        if role is None:
            role = RoleModel(
                name=role_data["name"], description=role_data["description"]
            )
            session.add(role)
            roles_created += 1
            await session.flush()
        else:
            role.description = role_data["description"]

        existing_permission_ids = set(
            (
                await session.scalars(
                    select(role_permissions.c.permission_id).where(
                        role_permissions.c.role_id == role.id
                    )
                )
            ).all()
        )
        for permission_key in role_data["permissions"]:
            permission = permissions[permission_key]
            if permission.id not in existing_permission_ids:
                await session.execute(
                    insert(role_permissions).values(
                        role_id=role.id, permission_id=permission.id
                    )
                )
                role_permissions_created += 1

    business_clock = await session.get(BusinessClock, 1)
    business_clock_created = business_clock is None
    if business_clock_created:
        session.add(BusinessClock(id=1))

    await session.flush()
    return ReferenceSeedResult(
        permissions_created=permissions_created,
        roles_created=roles_created,
        role_permissions_created=role_permissions_created,
        business_clock_created=business_clock_created,
    )


async def run_reference_seed() -> ReferenceSeedResult:
    """Run the seed through the configured application database connection."""
    bootstrap_orm()
    init_db_engine()
    try:
        async for session in get_db():
            try:
                result = await seed_reference_data(session)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    finally:
        await dispose_db_engine()


def main() -> None:
    result = asyncio.run(run_reference_seed())
    print(
        "reference bootstrap seed complete "
        f"(permissions={result.permissions_created}, roles={result.roles_created}, "
        f"role_permissions={result.role_permissions_created}, "
        f"business_clock_created={result.business_clock_created})"
    )


if __name__ == "__main__":
    main()
