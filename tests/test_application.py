import pytest
from qakeapi.core.application import ASGIApplication
from qakeapi.core.router import Router
from qakeapi.core.responses import Response

@pytest.mark.asyncio
class TestASGIApplication:
    async def test_http_request(self):
        app = ASGIApplication()
        router = Router()
        
        # Добавляем тестовый маршрут
        @router.route("/")
        async def test_handler(request):
            return Response({"message": "Hello, World!"}, status_code=200)
        
        app.router = router
        
        # Создаем тестовый scope
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }
        
        # Создаем тестовые receive и send функции
        received_messages = []
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
            
        async def send(message):
            received_messages.append(message)
            
        # Вызываем приложение
        await app(scope, receive, send)
        
        # Проверяем ответ
        assert len(received_messages) == 2
        assert received_messages[0]["type"] == "http.response.start"
        assert received_messages[0]["status"] == 200
        assert received_messages[1]["type"] == "http.response.body"
        assert received_messages[1]["body"] == b'{"message": "Hello, World!"}'
        
    async def test_websocket_request(self):
        app = ASGIApplication()
        
        # Создаем тестовый scope
        scope = {
            "type": "websocket",
            "path": "/ws",
            "headers": [],
        }
        
        # Создаем тестовые receive и send функции
        received_messages = []
        
        async def receive():
            return {"type": "websocket.connect"}
            
        async def send(message):
            received_messages.append(message)
            
        # Вызываем приложение
        await app(scope, receive, send)
        
        # Проверяем ответ
        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "websocket.close"
        
    async def test_lifespan_events(self):
        app = ASGIApplication()
        
        # Создаем тестовый scope
        scope = {
            "type": "lifespan",
        }
        
        # Создаем тестовые receive и send функции
        received_messages = []
        startup_complete = False
        shutdown_complete = False
        
        async def receive():
            nonlocal startup_complete, shutdown_complete
            if not startup_complete:
                startup_complete = True
                return {"type": "lifespan.startup"}
            if not shutdown_complete:
                shutdown_complete = True
                return {"type": "lifespan.shutdown"}
            return {"type": "lifespan.shutdown"}  # Никогда не должны дойти сюда
            
        async def send(message):
            received_messages.append(message)
            
        # Вызываем приложение
        await app(scope, receive, send)
        
        # Проверяем ответы
        assert len(received_messages) == 2
        assert received_messages[0]["type"] == "lifespan.startup.complete"
        assert received_messages[1]["type"] == "lifespan.shutdown.complete" 