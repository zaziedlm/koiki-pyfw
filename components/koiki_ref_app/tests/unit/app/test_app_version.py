from __future__ import annotations

import asyncio

from koiki_ref_app import app_factory


def test_app_exposes_release_version_in_metadata_and_status_endpoints() -> None:
    app = app_factory.create_app()
    routes = {route.path: route for route in app.routes}

    health = asyncio.run(routes["/health"].endpoint(None))
    root = asyncio.run(routes["/"].endpoint(None))

    assert app.version == "0.8.1"
    assert app.openapi()["info"]["version"] == "0.8.1"
    assert health["version"] == "0.8.1"
    assert root["version"] == "0.8.1"
