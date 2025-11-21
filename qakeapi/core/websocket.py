"""
WebSocket support for the framework.

This module provides WebSocket class and WebSocket route handling.
"""

import json
from typing import Any, Dict, Optional, AsyncIterator
from enum import Enum


class WebSocketState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocket:
    """
    WebSocket connection wrapper.
    
    Provides convenient interface for WebSocket operations.
    """
    
    def __init__(self, scope: Dict[str, Any], receive: Any, send: Any):
        """
        Initialize WebSocket connection.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        self.scope = scope
        self.receive = receive
        self.send = send
        self.state = WebSocketState.CONNECTING
        self.client = scope.get("client")
        self.path = scope.get("path", "/")
        self.query_params = self._parse_query_string(scope.get("query_string", b""))
        self.headers = self._parse_headers(scope.get("headers", []))
    
    def _parse_query_string(self, query_string: bytes) -> Dict[str, str]:
        """Parse query string to dictionary."""
        import urllib.parse
        if not query_string:
            return {}
        
        parsed = urllib.parse.parse_qs(query_string.decode(), keep_blank_values=True)
        return {k: v[0] if v else "" for k, v in parsed.items()}
    
    def _parse_headers(self, headers: list) -> Dict[str, str]:
        """Parse headers to dictionary."""
        result = {}
        for key, value in headers:
            key_str = key.decode().lower()
            value_str = value.decode()
            result[key_str] = value_str
        return result
    
    async def accept(
        self,
        subprotocol: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Accept WebSocket connection.
        
        Args:
            subprotocol: Optional subprotocol
            headers: Optional headers
        """
        if self.state != WebSocketState.CONNECTING:
            raise RuntimeError("WebSocket is not in CONNECTING state")
        
        message = {
            "type": "websocket.accept",
        }
        
        if subprotocol:
            message["subprotocol"] = subprotocol
        
        if headers:
            message_headers = []
            for key, value in headers.items():
                message_headers.append([key.encode(), value.encode()])
            message["headers"] = message_headers
        
        await self.send(message)
        self.state = WebSocketState.CONNECTED
    
    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        """
        Close WebSocket connection.
        
        Args:
            code: Close code
            reason: Optional close reason
        """
        if self.state != WebSocketState.CONNECTED:
            return
        
        message = {
            "type": "websocket.close",
            "code": code,
        }
        
        if reason:
            message["reason"] = reason
        
        await self.send(message)
        self.state = WebSocketState.DISCONNECTED
    
    async def send_text(self, data: str) -> None:
        """
        Send text message.
        
        Args:
            data: Text data to send
        """
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")
        
        await self.send({
            "type": "websocket.send",
            "text": data,
        })
    
    async def send_bytes(self, data: bytes) -> None:
        """
        Send binary message.
        
        Args:
            data: Binary data to send
        """
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")
        
        await self.send({
            "type": "websocket.send",
            "bytes": data,
        })
    
    async def send_json(self, data: Any) -> None:
        """
        Send JSON message.
        
        Args:
            data: Data to serialize as JSON
        """
        text = json.dumps(data, ensure_ascii=False)
        await self.send_text(text)
    
    async def receive_text(self) -> str:
        """
        Receive text message.
        
        Returns:
            Received text
        """
        message = await self.receive()
        
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise ConnectionError("WebSocket disconnected")
        
        if message["type"] == "websocket.connect":
            # If we get connect message, it means connection wasn't accepted yet
            # This shouldn't happen in normal flow, but handle it gracefully
            raise RuntimeError("WebSocket connection not accepted")
        
        if message["type"] != "websocket.receive":
            raise ValueError(f"Unexpected message type: {message['type']}")
        
        if "text" not in message:
            raise ValueError("Expected text message")
        
        return message["text"]
    
    async def receive_bytes(self) -> bytes:
        """
        Receive binary message.
        
        Returns:
            Received bytes
        """
        message = await self.receive()
        
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise ConnectionError("WebSocket disconnected")
        
        if message["type"] == "websocket.connect":
            # If we get connect message, it means connection wasn't accepted yet
            # This shouldn't happen in normal flow, but handle it gracefully
            raise RuntimeError("WebSocket connection not accepted")
        
        if message["type"] != "websocket.receive":
            raise ValueError(f"Unexpected message type: {message['type']}")
        
        if "bytes" not in message:
            raise ValueError("Expected binary message")
        
        return message["bytes"]
    
    async def receive_json(self) -> Dict[str, Any]:
        """
        Receive JSON message.
        
        Returns:
            Parsed JSON as dictionary
        """
        text = await self.receive_text()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
    
    async def iter_text(self) -> AsyncIterator[str]:
        """
        Iterate over text messages.
        
        Yields:
            Text messages
        """
        while self.state == WebSocketState.CONNECTED:
            try:
                yield await self.receive_text()
            except ConnectionError:
                break
    
    async def iter_json(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Iterate over JSON messages.
        
        Yields:
            Parsed JSON messages
        """
        while self.state == WebSocketState.CONNECTED:
            try:
                yield await self.receive_json()
            except ConnectionError:
                break

