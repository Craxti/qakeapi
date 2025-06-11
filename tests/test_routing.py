import pytest
from qakeapi.core.router import Router, Route
from typing import Dict, Any

@pytest.fixture
def router():
    return Router()

async def test_handler(request: Dict[str, Any]):
    return {
        "status": 200,
        "headers": [(b"content-type", b"application/json")],
        "body": b'{"message": "test"}'
    }

def test_route_creation():
    """Тест создания маршрута"""
    route = Route(
        path="/test",
        handler=test_handler,
        methods=["GET"]
    )
    assert route.path == "/test"
    assert route.methods == ["GET"]
    assert route.handler == test_handler

def test_route_pattern_compilation():
    """Тест компиляции паттерна маршрута"""
    route = Route(
        path="/users/{user_id}/posts/{post_id}",
        handler=test_handler,
        methods=["GET"]
    )
    assert route.pattern.pattern == '^/users/(?P<user_id>[^/]+)/posts/(?P<post_id>[^/]+)$'

def test_route_matching():
    """Тест сопоставления маршрута"""
    route = Route(
        path="/users/{user_id}",
        handler=test_handler,
        methods=["GET"]
    )
    
    # Проверяем успешное сопоставление
    match = route.match("/users/123")
    assert match == {"user_id": "123"}
    
    # Проверяем неуспешное сопоставление
    assert route.match("/posts/123") is None

def test_router_add_route(router):
    """Тест добавления маршрута в роутер"""
    router.add_route("/test", test_handler, ["GET"])
    assert len(router.routes) == 1
    assert router.routes[0].path == "/test"
    assert router.routes[0].methods == ["GET"]

@pytest.mark.asyncio
async def test_router_handle_request(router):
    """Тест обработки запроса роутером"""
    # Добавляем тестовый маршрут
    router.add_route("/test", test_handler, ["GET"])
    
    # Создаем тестовый запрос
    request = {
        "method": "GET",
        "path": "/test",
        "headers": {},
        "query_params": {},
        "body": b""
    }
    
    # Проверяем успешную обработку
    response = await router.handle_request(request)
    assert response["status"] == 200
    assert response["body"] == b'{"message": "test"}'
    
    # Проверяем обработку несуществующего маршрута
    request["path"] = "/nonexistent"
    response = await router.handle_request(request)
    assert response["status"] == 404

def test_router_find_route(router):
    """Тест поиска маршрута"""
    router.add_route("/users/{user_id}", test_handler, ["GET"])
    
    # Проверяем успешный поиск
    route, params = router.find_route("/users/123", "GET")
    assert route is not None
    assert params == {"user_id": "123"}
    
    # Проверяем неуспешный поиск
    route, params = router.find_route("/posts/123", "GET")
    assert route is None
    assert params is None

@pytest.mark.asyncio
class TestRouter:
    async def test_route_matching(self):
        router = Router()
        
        # Добавляем тестовый маршрут
        @router.route("/users/{user_id}")
        async def get_user(request):
            return {
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
                "body": f'{{"user_id": "{request["path_params"]["user_id"]}"}}'.encode()
            }
            
        # Тестируем совпадение маршрута
        request = {
            "path": "/users/123",
            "method": "GET"
        }
        response = await router.handle_request(request)
        
        assert response["status"] == 200
        assert response["body"] == b'{"user_id": "123"}'
        
    async def test_route_not_found(self):
        router = Router()
        
        # Тестируем несуществующий маршрут
        request = {
            "path": "/not/found",
            "method": "GET"
        }
        response = await router.handle_request(request)
        
        assert response["status"] == 404
        assert response["body"] == b'{"detail": "Not Found"}'
        
    async def test_route_methods(self):
        router = Router()
        
        # Добавляем тестовый маршрут с методами
        @router.route("/users", methods=["POST"])
        async def create_user(request):
            return {
                "status": 201,
                "headers": [(b"content-type", b"application/json")],
                "body": b'{"status": "created"}'
            }
            
        # Тестируем правильный метод
        request = {
            "path": "/users",
            "method": "POST"
        }
        response = await router.handle_request(request)
        
        assert response["status"] == 201
        assert response["body"] == b'{"status": "created"}'
        
        # Тестируем неправильный метод
        request = {
            "path": "/users",
            "method": "GET"
        }
        response = await router.handle_request(request)
        
        assert response["status"] == 404
        
    async def test_middleware(self):
        router = Router()
        
        # Добавляем тестовый middleware
        @router.middleware()
        def auth_middleware(handler):
            async def wrapper(request):
                if "Authorization" not in request["headers"]:
                    return {
                        "status": 401,
                        "headers": [(b"content-type", b"application/json")],
                        "body": b'{"detail": "Unauthorized"}'
                    }
                return await handler(request)
            return wrapper
            
        # Добавляем тестовый маршрут
        @router.route("/protected")
        async def protected_route(request):
            return {
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
                "body": b'{"status": "ok"}'
            }
            
        # Тестируем запрос без авторизации
        request = {
            "path": "/protected",
            "method": "GET",
            "headers": {}
        }
        response = await router.handle_request(request)
        
        assert response["status"] == 401
        assert response["body"] == b'{"detail": "Unauthorized"}'
        
        # Тестируем запрос с авторизацией
        request = {
            "path": "/protected",
            "method": "GET",
            "headers": {"Authorization": "Bearer token"}
        }
        response = await router.handle_request(request)
        
        assert response["status"] == 200
        assert response["body"] == b'{"status": "ok"}' 