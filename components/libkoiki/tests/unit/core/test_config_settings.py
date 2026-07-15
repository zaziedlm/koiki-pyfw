from libkoiki.core.config import Settings


def test_access_token_expire_minutes_default_is_short_lived(monkeypatch):
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

    settings = Settings(_env_file=None)

    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30


def test_auth_data_cleanup_defaults_are_safe_retention_values():
    settings = Settings(_env_file=None)

    assert settings.AUTH_DATA_CLEANUP_INTERVAL_SECONDS == 300
    assert settings.LOGIN_ATTEMPT_RETENTION_DAYS == 30


def test_csrf_secret_is_separate_from_jwt_secret_by_default(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("AUTH_CSRF_SECRET", raising=False)

    settings = Settings(_env_file=None)

    assert settings.AUTH_CSRF_SECRET != settings.JWT_SECRET


def test_refresh_cookie_path_defaults_to_route_prefix(monkeypatch):
    monkeypatch.delenv("AUTH_REFRESH_COOKIE_PATH", raising=False)

    settings = Settings(_env_file=None)

    assert settings.AUTH_REFRESH_COOKIE_PATH is None


def test_database_url_is_built_from_postgres_settings_when_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(
        _env_file=None,
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_pass",
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT=15432,
        POSTGRES_DB="test_db",
    )

    assert (
        settings.DATABASE_URL
        == "postgresql+asyncpg://test_user:test_pass@localhost:15432/test_db"
    )


def test_explicit_database_url_is_preserved():
    database_url = "postgresql+asyncpg://explicit:pass@db.example.com:5432/app"

    settings = Settings(_env_file=None, DATABASE_URL=database_url)

    assert settings.DATABASE_URL == database_url


def test_backend_cors_origins_accepts_comma_separated_string():
    settings = Settings(
        _env_file=None,
        BACKEND_CORS_ORIGINS="http://localhost:3000,https://example.com",
    )

    assert settings.BACKEND_CORS_ORIGINS == [
        "http://localhost:3000",
        "https://example.com",
    ]


def test_backend_cors_origins_strips_trailing_slash_from_list_items():
    settings = Settings(
        _env_file=None,
        BACKEND_CORS_ORIGINS=[
            "http://localhost:3000/",
            "https://example.com/",
        ],
    )

    assert settings.BACKEND_CORS_ORIGINS == [
        "http://localhost:3000",
        "https://example.com",
    ]
