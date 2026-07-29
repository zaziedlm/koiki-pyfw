"""application-health capability: /health, / のアプリ識別情報応答。"""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from koiki_ref_app import app_factory
from libkoiki.core.config import settings


@pytest.fixture
def health_client(monkeypatch):
    monkeypatch.setattr(app_factory, "connect_db", AsyncMock())
    monkeypatch.setattr(app_factory, "disconnect_db", AsyncMock())
    monkeypatch.setattr(app_factory.settings, "REDIS_ENABLED", False)
    monkeypatch.setattr(app_factory.settings, "RATE_LIMIT_ENABLED", False)

    app = app_factory.create_app()
    with TestClient(app) as client:
        yield client


def test_health_endpoint_returns_app_identity(health_client: TestClient) -> None:
    response = health_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == settings.APP_NAME
    assert body["version"] == health_client.app.version


def test_root_endpoint_returns_app_identity(health_client: TestClient) -> None:
    response = health_client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == settings.APP_NAME
    assert body["version"] == health_client.app.version


def test_health_service_follows_app_name_change(
    monkeypatch: pytest.MonkeyPatch, health_client: TestClient
) -> None:
    monkeypatch.setattr(settings, "APP_NAME", "Test App Name")

    response = health_client.get("/health")

    assert response.json()["service"] == "Test App Name"
