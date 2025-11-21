"""
Tests for WebSocket support.
"""

import pytest
from qakeapi import QakeAPI, WebSocket


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection."""
    app = QakeAPI()

    @app.websocket("/ws")
    async def websocket_handler(websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text("Hello")
        await websocket.close()

    # Create mock WebSocket scope
    scope = {
        "type": "websocket",
        "path": "/ws",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
    }

    messages = []

    async def receive():
        if len(messages) == 0:
            # First message - connection
            return {"type": "websocket.connect"}
        elif len(messages) == 1:
            # After accept - send message
            return {"type": "websocket.receive", "text": "test"}
        else:
            # Disconnect
            return {"type": "websocket.disconnect", "code": 1000}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    # Check messages
    assert len(messages) >= 2
    assert messages[0]["type"] == "websocket.accept"
    assert messages[-1]["type"] == "websocket.close"


@pytest.mark.asyncio
async def test_websocket_send_receive():
    """Test WebSocket send and receive."""
    from qakeapi.core.websocket import WebSocket

    scope = {
        "type": "websocket",
        "path": "/ws",
        "query_string": b"",
        "headers": [],
    }

    message_queue = [
        {"type": "websocket.receive", "text": "Hello"},
        {"type": "websocket.disconnect"},
    ]
    message_index = 0

    async def receive():
        nonlocal message_index
        if message_index < len(message_queue):
            msg = message_queue[message_index]
            message_index += 1
            return msg
        return {"type": "websocket.disconnect"}

    sent_messages = []

    async def send(message):
        sent_messages.append(message)

    websocket = WebSocket(scope, receive, send)

    # Accept connection
    await websocket.accept()
    assert websocket.state.value == "connected"

    # Send text
    await websocket.send_text("Test")
    assert len(sent_messages) > 0

    # Receive text
    text = await websocket.receive_text()
    assert text == "Hello"


@pytest.mark.asyncio
async def test_websocket_json():
    """Test WebSocket JSON messages."""
    from qakeapi.core.websocket import WebSocket

    scope = {
        "type": "websocket",
        "path": "/ws",
        "query_string": b"",
        "headers": [],
    }

    message_queue = [
        {"type": "websocket.receive", "text": '{"message": "test"}'},
        {"type": "websocket.disconnect"},
    ]
    message_index = 0

    async def receive():
        nonlocal message_index
        if message_index < len(message_queue):
            msg = message_queue[message_index]
            message_index += 1
            return msg
        return {"type": "websocket.disconnect"}

    sent_messages = []

    async def send(message):
        sent_messages.append(message)

    websocket = WebSocket(scope, receive, send)

    await websocket.accept()

    # Send JSON
    await websocket.send_json({"type": "hello", "data": "world"})

    # Receive JSON
    data = await websocket.receive_json()
    assert data == {"message": "test"}
