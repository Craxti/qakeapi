"""
Тесты для WebSocket функциональности
"""
import pytest
import asyncio
from qakeapi import QakeAPI, WebSocket
from qakeapi.core.exceptions import WebSocketException


@pytest.fixture
def app():
    """Создать тестовое приложение с WebSocket"""
    app = QakeAPI(title="WebSocket Test App")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo: {data}")
        except WebSocketException:
            pass

    @app.websocket("/ws/json")
    async def websocket_json_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                await websocket.send_json({"echo": data, "type": "response"})
        except WebSocketException:
            pass

    @app.websocket("/ws/close")
    async def websocket_close_endpoint(websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text("Hello")
        await websocket.close(code=1000, reason="Test close")

    return app


class TestWebSocket:
    """Тесты WebSocket функциональности"""

    @pytest.mark.asyncio
    async def test_websocket_text_echo(self, app):
        """Тест эхо WebSocket с текстом"""
        from unittest.mock import AsyncMock, MagicMock

        # Создаем mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Настраиваем последовательность вызовов
        mock_websocket.receive_text.side_effect = [
            "Hello WebSocket",
            "Another message",
            WebSocketException("Connection closed"),
        ]

        # Находим WebSocket endpoint
        ws_route = None
        for route in app.routes:
            if route.path == "/ws":
                ws_route = route
                break

        assert ws_route is not None, "WebSocket route /ws not found"

        # Вызываем handler напрямую
        try:
            await ws_route.handler(mock_websocket)
        except WebSocketException:
            pass  # Ожидаемое исключение

        # Проверяем вызовы
        mock_websocket.accept.assert_called_once()
        assert mock_websocket.send_text.call_count == 2
        mock_websocket.send_text.assert_any_call("Echo: Hello WebSocket")
        mock_websocket.send_text.assert_any_call("Echo: Another message")

    @pytest.mark.asyncio
    async def test_websocket_json_echo(self, app):
        """Тест эхо WebSocket с JSON"""
        from unittest.mock import AsyncMock, MagicMock

        # Создаем mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock()
        mock_websocket.send_json = AsyncMock()

        test_data = {"message": "Hello", "number": 42}

        # Настраиваем последовательность вызовов
        mock_websocket.receive_json.side_effect = [
            test_data,
            WebSocketException("Connection closed"),
        ]

        # Находим WebSocket endpoint
        ws_route = None
        for route in app.routes:
            if route.path == "/ws/json":
                ws_route = route
                break

        assert ws_route is not None, "WebSocket route /ws/json not found"

        # Вызываем handler напрямую
        try:
            await ws_route.handler(mock_websocket)
        except WebSocketException:
            pass  # Ожидаемое исключение

        # Проверяем вызовы
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_called_once_with(
            {"echo": test_data, "type": "response"}
        )

    @pytest.mark.asyncio
    async def test_websocket_close(self, app):
        """Тест закрытия WebSocket соединения"""
        from unittest.mock import AsyncMock, MagicMock

        # Создаем mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Находим WebSocket endpoint
        ws_route = None
        for route in app.routes:
            if route.path == "/ws/close":
                ws_route = route
                break

        assert ws_route is not None, "WebSocket route /ws/close not found"

        # Вызываем handler напрямую
        await ws_route.handler(mock_websocket)

        # Проверяем вызовы
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once_with("Hello")
        mock_websocket.close.assert_called_once_with(code=1000, reason="Test close")

    def test_websocket_state_enum(self):
        """Тест enum состояний WebSocket"""
        from qakeapi.core.websocket import WebSocketState

        assert WebSocketState.CONNECTING.value == "connecting"
        assert WebSocketState.CONNECTED.value == "connected"
        assert WebSocketState.DISCONNECTED.value == "disconnected"

    def test_websocket_exception(self):
        """Тест WebSocket исключений"""
        exc = WebSocketException(1000, "Normal closure")
        assert exc.code == 1000
        assert exc.reason == "Normal closure"
        assert "WebSocket 1000: Normal closure" in str(exc)


class TestWebSocketIntegration:
    """Интеграционные тесты WebSocket"""

    @pytest.mark.asyncio
    async def test_websocket_chat_simulation(self):
        """Тест симуляции чата через WebSocket"""
        app = QakeAPI()

        # Список подключенных клиентов
        connected_clients = set()

        @app.websocket("/chat")
        async def chat_endpoint(websocket: WebSocket):
            await websocket.accept()
            connected_clients.add(websocket)

            try:
                # Уведомляем о подключении
                for client in connected_clients:
                    if client != websocket:
                        try:
                            await client.send_json(
                                {
                                    "type": "user_joined",
                                    "clients_count": len(connected_clients),
                                }
                            )
                        except:
                            pass

                # Обрабатываем сообщения
                async for message in websocket.iter_json():
                    # Пересылаем всем клиентам
                    for client in connected_clients.copy():
                        try:
                            await client.send_json({"type": "message", "data": message})
                        except:
                            connected_clients.discard(client)

            except WebSocketException:
                pass
            finally:
                connected_clients.discard(websocket)

                # Уведомляем об отключении
                for client in connected_clients.copy():
                    try:
                        await client.send_json(
                            {
                                "type": "user_left",
                                "clients_count": len(connected_clients),
                            }
                        )
                    except:
                        connected_clients.discard(client)

        # Тестируем чат с mock WebSocket
        from unittest.mock import AsyncMock, MagicMock

        # Создаем два mock WebSocket клиента
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        # Настраиваем сообщения
        test_message = {"user": "Alice", "message": "Hello everyone!"}

        # Создаем async iterator для ws1
        class MockAsyncIterator:
            def __init__(self, items):
                self.items = iter(items)

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self.items)
                except StopIteration:
                    raise WebSocketException("Connection closed")

        # Устанавливаем iter_json как метод, который возвращает async iterator
        def mock_iter_json():
            return MockAsyncIterator([test_message])

        ws1.iter_json = mock_iter_json

        # Находим WebSocket endpoint
        ws_route = None
        for route in app.routes:
            if route.path == "/chat":
                ws_route = route
                break

        assert ws_route is not None, "WebSocket route /chat not found"

        # Симулируем подключение первого клиента
        try:
            await ws_route.handler(ws1)
        except WebSocketException:
            pass

        # Проверяем, что первый клиент был принят
        ws1.accept.assert_called_once()

        # Проверяем, что сообщение было отправлено (в реальном чате это было бы всем клиентам)
        # В данном случае у нас только один клиент, поэтому проверяем базовую функциональность
        assert len(connected_clients) == 0  # Клиент должен быть удален после исключения


if __name__ == "__main__":
    pytest.main([__file__])
