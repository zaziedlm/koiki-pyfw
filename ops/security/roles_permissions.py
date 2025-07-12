"""
KOIKI-FW セキュリティ権限・ロール定義
セキュリティ監視API用の権限管理データ定義
"""

# 基本権限の定義
BASIC_PERMISSIONS = {
    # セキュリティ監視権限
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
    # ユーザー管理権限
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
    # ToDo管理権限
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
    # システム管理権限
    "admin:system": {
        "name": "admin:system",
        "description": "システム全体の管理者権限",
        "resource": "system",
        "action": "admin",
    },
}

# 基本ロールの定義
BASIC_ROLES = {
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
        "permissions": [
            "admin:system",
            "read:security_metrics",
            "manage:security_metrics",
            "read:users",
            "write:users",
            "read:todos",
            "write:todos",
        ],
    },
}

# 初期ユーザーとロールのマッピング
INITIAL_USER_ROLES = {
    "admin@example.com": ["system_admin"],  # スーパーユーザー
    "security@example.com": ["security_admin"],  # セキュリティ管理者
    "user_admin@example.com": ["user_admin"],  # ユーザー管理者
    "user@example.com": ["todo_user"],  # 一般ユーザー
}

# テスト用ユーザーデータ
TEST_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123456",
        "is_superuser": True,
        "is_active": True,
    },
    {
        "username": "security",
        "email": "security@example.com",
        "password": "security123456",
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "useradmin",
        "email": "user_admin@example.com",
        "password": "useradmin123456",
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "testuser",
        "email": "user@example.com",
        "password": "testuser123456",
        "is_superuser": False,
        "is_active": True,
    },
]
