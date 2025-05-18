from setuptools import setup, find_packages

setup(
    name="libkoiki",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy[asyncio]",
        "asyncpg",
        "alembic",
        "pydantic",
        "pydantic-settings",
        "python-jose",
        "passlib[bcrypt]",
        "httpx",
        "structlog",
        "redis",
        "slowapi",
        "email-validator",
        "prometheus-client",
        "python-multipart",  # フォームデータ処理用に追加
    ],
)
