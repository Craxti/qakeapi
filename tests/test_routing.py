from typing import Any, Dict

import pytest

from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.core.routing import Route, Router


@pytest.fixture
def router():
    return Router()


async def mock_handler(request):
    return Response(content={"message": "test"})


def mock_middleware(handler):
    async def wrapped(request):
        request.middleware_called = True
        return await handler(request)
    return wrapped


def test_route_creation():
    route = Route("/test", mock_handler, ["GET"])
    assert route.path == "/test"
    assert route.handler == mock_handler
    assert route.methods == ["GET"]
    assert route.name is None
    assert route.type == "http"


def test_route_pattern_compilation():
    route = Route("/users/{id}", mock_handler, ["GET"])
    assert route.pattern.pattern == r"^/users/(?P<id>[^/]+)$"


def test_route_match():
    route = Route("/users/{id}", mock_handler, ["GET"])
    
    # Test matching path
    match = route.match("/users/123")
    assert match == {"id": "123"}
    
    # Test non-matching path
    match = route.match("/posts/123")
    assert match is None


def test_route_match_multiple_params():
    route = Route("/users/{user_id}/posts/{post_id}", mock_handler, ["GET"])
    
    match = route.match("/users/123/posts/456")
    assert match == {"user_id": "123", "post_id": "456"}


@pytest.mark.asyncio
async def test_router_basic():
    router = Router()
    router.add_route("/test", mock_handler, ["GET"])
    
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })
    response = await router.handle_request(request)
    
    assert response.status_code == 200
    body = await response.body
    assert b"test" in body


@pytest.mark.asyncio
async def test_router_not_found():
    router = Router()
    router.add_route("/test", mock_handler, ["GET"])
    
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/nonexistent",
        "headers": [],
        "query_string": b"",
    })
    response = await router.handle_request(request)
    
    assert response.status_code == 404
    body = await response.body
    assert b"Not Found" in body


def test_router_route_decorator():
    router = Router()
    
    @router.route("/test", methods=["GET"])
    async def test_handler(request):
        return Response(content={"message": "test"})
    
    route = router.routes[0]
    assert route.path == "/test"
    assert route.methods == ["GET"]


@pytest.mark.asyncio
async def test_router_middleware():
    router = Router()
    router.add_route("/test", mock_handler, ["GET"])
    router.add_middleware(mock_middleware)

    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })

    response = await router.handle_request(request)
    assert response.status_code == 200
    assert hasattr(request, "middleware_called")
    assert request.middleware_called is True


def test_router_middleware_decorator():
    router = Router()
    
    @router.middleware()
    async def test_middleware(handler):
        async def wrapped(request):
            request.middleware_called = True
            return await handler(request)
        return wrapped
    
    assert len(router._middleware) == 1


def test_router_url_for():
    router = Router()
    router.add_route("/users/{id}", mock_handler, ["GET"])
    router.routes[0].name = "user_detail"
    
    url = router.url_for("user_detail", id=123)
    assert url == "/users/123"


def test_router_url_for_not_found():
    router = Router()
    
    with pytest.raises(ValueError):
        router.url_for("nonexistent")


def test_router_websocket_route():
    router = Router()
    router.add_websocket_route("/ws", mock_handler)
    
    route = router.routes[0]
    assert route.type == "websocket"
    assert route.path == "/ws"


def test_route_match_complex_path():
    route = Route("/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}", 
                  mock_handler, ["GET"])
    
    match = route.match("/api/v1/users/123/posts/456/comments/789")
    assert match == {
        "user_id": "123",
        "post_id": "456",
        "comment_id": "789"
    }


@pytest.mark.asyncio
async def test_router_method_not_allowed():
    router = Router()
    router.add_route("/test", mock_handler, ["GET"])

    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })
    response = await router.handle_request(request)

    assert response.status_code == 405  # Method Not Allowed
    body = await response.body
    assert b"Method Not Allowed" in body


def test_route_match_empty_path():
    route = Route("/", mock_handler, ["GET"])
    
    match = route.match("/")
    assert match == {}
    
    match = route.match("/test")
    assert match is None


def test_router_add_route(router):
    """Тест добавления маршрута в роутер"""
    router.add_route("/test", mock_handler, ["GET"])
    assert len(router.routes) == 1
    assert router.routes[0].path == "/test"
    assert router.routes[0].methods == ["GET"]


@pytest.mark.asyncio
async def test_router_handle_request(router):
    """Тест обработки запроса роутером"""
    # Добавляем тестовый маршрут
    router.add_route("/test", mock_handler, ["GET"])

    # Создаем тестовый запрос
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        }
    )

    # Проверяем успешную обработку
    response = await router.handle_request(request)
    assert response.status_code == 200


def test_router_find_route(router):
    """Тест поиска маршрута"""
    router.add_route("/users/{user_id}", mock_handler, ["GET"])

    # Проверяем успешный поиск
    route_info = router.find_route("/users/123", "http")
    assert route_info is not None
    route, params = route_info
    assert route.handler == mock_handler
    assert params["user_id"] == "123"

    # Проверяем отсутствие маршрута
    assert router.find_route("/not/found", "http") is None


@pytest.mark.asyncio
class TestRouter:
    async def test_route_matching(self):
        router = Router()

        # Добавляем тестовый маршрут
        @router.route("/users/{user_id}")
        async def get_user(request):
            user_id = request.path_params.get("user_id")
            return Response({"user_id": user_id}, status_code=200)

        # Тестируем совпадение маршрута
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/users/123",
                "headers": [],
                "query_string": b"",
                "path_params": {},  # Инициализируем path_params в scope
            }
        )
        response = await router.handle_request(request)

        assert response.status_code == 200
        body = await response.body
        assert b"123" in body  # Проверяем, что user_id правильно передан

    async def test_route_not_found(self):
        router = Router()

        # Тестируем несуществующий маршрут
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/not/found",
                "headers": [],
                "query_string": b"",
            }
        )
        response = await router.handle_request(request)

        assert response.status_code == 404

    async def test_route_methods(self):
        router = Router()

        # Добавляем тестовый маршрут с методами
        @router.route("/users", methods=["POST"])
        async def create_user(request):
            return Response({"status": "created"}, status_code=201)

        # Тестируем правильный метод
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/users",
                "headers": [],
                "query_string": b"",
            }
        )
        response = await router.handle_request(request)

        assert response.status_code == 201

    async def test_middleware(self):
        router = Router()

        # Добавляем тестовый middleware
        @router.middleware()
        def auth_middleware(handler):
            async def wrapper(request):
                if "Authorization" not in request.headers:
                    return Response({"detail": "Unauthorized"}, status_code=401)
                return await handler(request)

            return wrapper

        # Добавляем тестовый маршрут
        @router.route("/protected")
        async def protected_route(request):
            return Response({"status": "ok"}, status_code=200)

        # Тестируем запрос без авторизации
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/protected",
                "headers": [],
                "query_string": b"",
            }
        )
        response = await router.handle_request(request)

        assert response.status_code == 401
