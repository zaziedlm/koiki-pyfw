import pytest
from fastapi.routing import APIRoute

from libkoiki.api.dependencies import require_csrf_for_cookie_auth
from libkoiki.api.v1.endpoints import todos
from koiki_ref_app.api.v1.endpoints import business_clock


def _route_with_method(routes: list, *, path: str, method: str) -> APIRoute:
    for route in routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route
    raise AssertionError(f"Route not found: {method} {path}")


def _has_cookie_csrf_dependency(route: APIRoute) -> bool:
    return any(
        dependency.call is require_csrf_for_cookie_auth
        for dependency in route.dependant.dependencies
    )


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("", "POST"),
        ("/{todo_id}", "PUT"),
        ("/{todo_id}", "DELETE"),
    ],
)
def test_todos_unsafe_routes_require_cookie_csrf(path: str, method: str) -> None:
    route = _route_with_method(todos.router.routes, path=path, method=method)

    assert _has_cookie_csrf_dependency(route)


def test_business_clock_update_requires_cookie_csrf() -> None:
    route = _route_with_method(business_clock.router.routes, path="", method="POST")

    assert _has_cookie_csrf_dependency(route)
