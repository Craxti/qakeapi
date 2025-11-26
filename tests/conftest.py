"""
Pytest configuration and fixtures for QakeAPI tests.
"""

import pytest
from typing import Dict, Any

from qakeapi import QakeAPI, Request
from qakeapi.core.response import Response


@pytest.fixture
def app():
    """Create a test QakeAPI application."""
    return QakeAPI(title="Test API", version="1.2.0", debug=True)


@pytest.fixture
def scope():
    """Create a test ASGI scope."""
    return {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "scheme": "http",
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 12345),
        "headers": [],
        "query_string": b"",
    }


@pytest.fixture
async def receive():
    """Mock ASGI receive callable."""
    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    
    return _receive


@pytest.fixture
def send():
    """Mock ASGI send callable."""
    messages = []
    
    async def _send(message: Dict[str, Any]):
        messages.append(message)
    
    _send.messages = messages
    return _send


@pytest.fixture
def websocket_scope():
    """Create a test WebSocket ASGI scope."""
    return {
        "type": "websocket",
        "path": "/ws",
        "scheme": "ws",
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 12345),
        "headers": [],
        "subprotocols": [],
    }


@pytest.fixture
async def websocket_receive():
    """Mock WebSocket ASGI receive callable."""
    async def _receive():
        return {"type": "websocket.receive", "text": '{"message": "test"}'}
    
    return _receive


@pytest.fixture
def websocket_send():
    """Mock WebSocket ASGI send callable."""
    messages = []
    
    async def _send(message: Dict[str, Any]):
        messages.append(message)
    
    _send.messages = messages
    return _send


