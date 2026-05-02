from libkoiki.core.config import Settings


def test_database_url_is_built_from_postgres_settings_when_missing():
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

    assert [str(origin) for origin in settings.BACKEND_CORS_ORIGINS] == [
        "http://localhost:3000/",
        "https://example.com/",
    ]
