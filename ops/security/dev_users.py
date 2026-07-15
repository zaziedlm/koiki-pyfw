"""Development and E2E-only users with fixed passwords.

These values must never be imported by the reference bootstrap seed or an
application startup path.
"""

INITIAL_USER_ROLES = {
    "admin@example.com": ["system_admin"],
    "security@example.com": ["security_admin"],
    "user_admin@example.com": ["user_admin"],
    "user@example.com": ["todo_user"],
}

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
