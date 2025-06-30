import pytest
import pytest_asyncio
from qakeapi.core.websockets import WebSocket, WebSocketState
from qakeapi.core.application import Application


@pytest_asyncio.fixture
async def app():
    return Application()


@pytest_asyncio.fixture
async def websocket_client():
    async def mock_receive():
        return {"type": "websocket.connect"}

    async def mock_send(message):
        pass

    scope = {
        "type": "websocket",
        "path": "/ws",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 8000),
        "path_params": {},
    }

    return WebSocket(scope, mock_receive, mock_send)


class TestWebSocket:
    @pytest.mark.asyncio
    async def test_websocket_connection(self, websocket_client):
        assert websocket_client.state == WebSocketState.CONNECTING
        await websocket_client.accept()
        assert websocket_client.state == WebSocketState.CONNECTED

    @pytest.mark.asyncio
    async def test_websocket_send_receive(self, websocket_client):
        await websocket_client.accept()

        # Test sending text
        await websocket_client.send_text("Hello")
        assert websocket_client.state == WebSocketState.CONNECTED

        # Test sending JSON
        data = {"message": "Hello"}
        await websocket_client.send_json(data)
        assert websocket_client.state == WebSocketState.CONNECTED

    @pytest.mark.asyncio
    async def test_websocket_close(self, websocket_client):
        await websocket_client.accept()
        await websocket_client.close(code=1000)
        assert websocket_client.state == WebSocketState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, websocket_client):
        await websocket_client.accept()
        await websocket_client.send_ping(b"ping")
        # В реальном приложении здесь мы бы получили pong
        assert websocket_client.state == WebSocketState.CONNECTED


class TestWebSocketRouting:
    @pytest.mark.asyncio
    async def test_websocket_route(self, app):
        received_messages = []

        @app.websocket("/ws/test")
        async def websocket_handler(websocket: WebSocket):
            await websocket.accept()
            async for message in websocket:
                received_messages.append(message)
                await websocket.send_text(f"Echo: {message}")

        # Проверяем, что маршрут был зарегистрирован
        # В новой архитектуре роутеры находятся внутри приложения
        assert len(app.ws_router.routes) > 0
        
        # Проверяем, что есть маршрут с нужным путем
        found_route = None
        for route in app.ws_router.routes:
            if route.path == "/ws/test":
                found_route = route
                break
        
        assert found_route is not None
        assert found_route.handler == websocket_handler


class TestWebSocketMiddleware:
    @pytest.mark.asyncio
    async def test_websocket_middleware(self, app):
        @app.websocket("/ws/test")
        async def websocket_handler(websocket: WebSocket):
            await websocket.accept()

        # Создаем тестовый клиент
        async def mock_receive():
            return {"type": "websocket.connect"}

        async def mock_send(message):
            pass

        scope = {
            "type": "websocket",
            "path": "/ws/test",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 8000),
            "path_params": {},
        }

        # Проверяем выполнение middleware
        await app.handle_websocket(scope, mock_receive, mock_send)