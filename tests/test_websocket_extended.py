"""
Extended tests for WebSocket to increase coverage.
"""

import pytest
import json
from qakeapi.core.websocket import WebSocket


class TestWebSocketExtended:
    """Extended tests for WebSocket."""
    
    @pytest.mark.asyncio
    async def test_websocket_send_bytes(self, websocket_scope, websocket_receive, websocket_send):
        """Test sending bytes message."""
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        await websocket.accept()
        
        data = b"binary data"
        await websocket.send_bytes(data)
        
        messages = [m for m in websocket_send.messages if m["type"] == "websocket.send"]
        assert len(messages) == 1
        assert messages[0]["bytes"] == data
    
    @pytest.mark.asyncio
    async def test_websocket_receive_bytes(self, websocket_scope, websocket_send):
        """Test receiving bytes message."""
        data = b"binary data"
        
        async def receive():
            return {"type": "websocket.receive", "bytes": data}
        
        websocket = WebSocket(websocket_scope, receive, websocket_send)
        await websocket.accept()
        
        received = await websocket.receive_bytes()
        assert received == data
    
    @pytest.mark.asyncio
    async def test_websocket_iter_text(self, websocket_scope, websocket_send):
        """Test iterating over text messages."""
        messages = ["message1", "message2", "message3"]
        index = [0]
        
        async def receive():
            if index[0] < len(messages):
                result = {
                    "type": "websocket.receive",
                    "text": messages[index[0]],
                }
                index[0] += 1
                return result
            return {"type": "websocket.close"}
        
        websocket = WebSocket(websocket_scope, receive, websocket_send)
        await websocket.accept()
        
        received = []
        async for msg in websocket.iter_text():
            received.append(msg)
            if len(received) >= len(messages):
                break
        
        assert len(received) == len(messages)
        assert received == messages
    
    @pytest.mark.asyncio
    async def test_websocket_iter_json(self, websocket_scope, websocket_send):
        """Test iterating over JSON messages."""
        messages = [{"msg": "1"}, {"msg": "2"}]
        index = [0]
        
        async def receive():
            if index[0] < len(messages):
                result = {
                    "type": "websocket.receive",
                    "text": json.dumps(messages[index[0]]),
                }
                index[0] += 1
                return result
            return {"type": "websocket.close"}
        
        websocket = WebSocket(websocket_scope, receive, websocket_send)
        await websocket.accept()
        
        received = []
        async for msg in websocket.iter_json():
            received.append(msg)
            if len(received) >= len(messages):
                break
        
        assert len(received) == len(messages)
    
    @pytest.mark.asyncio
    async def test_websocket_close_on_receive(self, websocket_scope, websocket_send):
        """Test WebSocket close on receive."""
        async def receive():
            return {"type": "websocket.close", "code": 1000}
        
        websocket = WebSocket(websocket_scope, receive, websocket_send)
        await websocket.accept()
        
        with pytest.raises(ConnectionError):
            await websocket.receive_text()
    
    @pytest.mark.asyncio
    async def test_websocket_headers(self, websocket_scope, websocket_receive, websocket_send):
        """Test WebSocket headers."""
        websocket_scope["headers"] = [(b"authorization", b"Bearer token")]
        
        websocket = WebSocket(websocket_scope, websocket_receive, websocket_send)
        
        assert "authorization" in websocket.headers
        assert websocket.headers["authorization"] == "Bearer token"


