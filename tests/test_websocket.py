"""
Tests for WebSocket support.
"""

import pytest
import json
from qakeapi.core.websocket import WebSocket, WebSocketRoute


class TestWebSocket:
    """Tests for WebSocket class."""
    
    @pytest.mark.asyncio
    async def test_websocket_creation(self, websocket_scope, websocket_receive, websocket_send):
        """Test WebSocket creation."""
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        
        assert websocket.path == "/ws"
    
    @pytest.mark.asyncio
    async def test_websocket_accept(self, websocket_scope, websocket_receive, websocket_send):
        """Test WebSocket accept."""
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        
        await websocket.accept()
        
        assert len(websocket_send.messages) == 1
        assert websocket_send.messages[0]["type"] == "websocket.accept"
        assert websocket._accepted is True
    
    @pytest.mark.asyncio
    async def test_websocket_send_text(self, websocket_scope, websocket_receive, websocket_send):
        """Test sending text message."""
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        await websocket.accept()
        
        await websocket.send_text("Hello, World!")
        
        messages = [m for m in websocket_send.messages if m["type"] == "websocket.send"]
        assert len(messages) == 1
        assert messages[0]["text"] == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_websocket_send_json(self, websocket_scope, websocket_receive, websocket_send):
        """Test sending JSON message."""
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        await websocket.accept()
        
        data = {"message": "Hello", "status": "ok"}
        await websocket.send_json(data)
        
        messages = [m for m in websocket_send.messages if m["type"] == "websocket.send"]
        assert len(messages) == 1
        assert json.loads(messages[0]["text"]) == data
    
    @pytest.mark.asyncio
    async def test_websocket_receive_text(self, websocket_scope, websocket_send):
        """Test receiving text message."""
        async def receive():
            return {"type": "websocket.receive", "text": "Hello, World!"}
        
        websocket = WebSocket(websocket_scope, receive, websocket_send)
        await websocket.accept()
        
        message = await websocket.receive_text()
        assert message == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_websocket_receive_json(self, websocket_scope, websocket_send):
        """Test receiving JSON message."""
        data = {"message": "Hello", "status": "ok"}
        
        async def receive():
            return {"type": "websocket.receive", "text": json.dumps(data)}
        
        websocket = WebSocket(websocket_scope, receive, websocket_send)
        await websocket.accept()
        
        received_data = await websocket.receive_json()
        assert received_data == data
    
    @pytest.mark.asyncio
    async def test_websocket_close(self, websocket_scope, websocket_receive, websocket_send):
        """Test closing WebSocket."""
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        await websocket.accept()
        
        await websocket.close(code=1000)
        
        close_messages = [m for m in websocket_send.messages if m["type"] == "websocket.close"]
        assert len(close_messages) == 1
        assert close_messages[0]["code"] == 1000


class TestWebSocketRoute:
    """Tests for WebSocketRoute."""
    
    def test_websocket_route_creation(self):
        """Test WebSocket route creation."""
        async def handler(websocket):
            await websocket.accept()
        
        route = WebSocketRoute("/ws", handler)
        assert route.path == "/ws"
        assert route.handler == handler
    
    def test_websocket_route_match(self):
        """Test WebSocket route matching."""
        async def handler(websocket):
            await websocket.accept()
        
        route = WebSocketRoute("/ws", handler)
        assert route.match("/ws") == {}
        assert route.match("/other") is None
    
    def test_websocket_route_match_with_params(self):
        """Test WebSocket route matching with parameters."""
        async def handler(websocket, room: str):
            await websocket.accept()
        
        route = WebSocketRoute("/ws/{room}", handler)
        params = route.match("/ws/test-room")
        assert params == {"room": "test-room"}


