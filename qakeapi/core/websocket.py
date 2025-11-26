"""
WebSocket support for QakeAPI.

This module provides WebSocket functionality for real-time communication.
"""

import asyncio
import json
from typing import Any, AsyncIterator, Callable, Dict, Optional


class WebSocket:
    """
    WebSocket connection handler.
    
    Provides methods for accepting connections, sending/receiving messages,
    and managing WebSocket lifecycle.
    """
    
    def __init__(self, scope: Dict[str, Any], receive: Any, send: Any):
        """
        Initialize WebSocket.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        self.scope = scope
        self._receive = receive
        self._send = send
        self._accepted = False
        self._closed = False
    
    @property
    def path(self) -> str:
        """WebSocket path."""
        return self.scope.get("path", "/")
    
    @property
    def headers(self) -> Dict[str, str]:
        """WebSocket headers."""
        headers_dict = {}
        for key, value in self.scope.get("headers", []):
            key_str = key.decode() if isinstance(key, bytes) else key
            value_str = value.decode() if isinstance(value, bytes) else value
            headers_dict[key_str.lower()] = value_str
        return headers_dict
    
    async def accept(self, subprotocol: Optional[str] = None) -> None:
        """
        Accept WebSocket connection.
        
        Args:
            subprotocol: Optional subprotocol
        """
        if self._accepted:
            return
        
        message = {"type": "websocket.accept"}
        if subprotocol:
            message["subprotocol"] = subprotocol
        
        await self._send(message)
        self._accepted = True
    
    async def close(self, code: int = 1000) -> None:
        """
        Close WebSocket connection.
        
        Args:
            code: Close code
        """
        if self._closed:
            return
        
        await self._send({"type": "websocket.close", "code": code})
        self._closed = True
    
    async def send_text(self, text: str) -> None:
        """
        Send text message.
        
        Args:
            text: Text message to send
        """
        if not self._accepted:
            await self.accept()
        
        await self._send({"type": "websocket.send", "text": text})
    
    async def send_json(self, data: Any) -> None:
        """
        Send JSON message.
        
        Args:
            data: Data to send as JSON
        """
        text = json.dumps(data)
        await self.send_text(text)
    
    async def send_bytes(self, data: bytes) -> None:
        """
        Send binary message.
        
        Args:
            data: Binary data to send
        """
        if not self._accepted:
            await self.accept()
        
        await self._send({"type": "websocket.send", "bytes": data})
    
    async def receive_text(self) -> str:
        """
        Receive text message.
        
        Returns:
            Text message
        """
        message = await self._receive()
        
        if message["type"] == "websocket.close":
            raise ConnectionError("WebSocket closed")
        
        return message.get("text", "")
    
    async def receive_json(self) -> Any:
        """
        Receive JSON message.
        
        Returns:
            Parsed JSON data
        """
        text = await self.receive_text()
        return json.loads(text)
    
    async def receive_bytes(self) -> bytes:
        """
        Receive binary message.
        
        Returns:
            Binary data
        """
        message = await self._receive()
        
        if message["type"] == "websocket.close":
            raise ConnectionError("WebSocket closed")
        
        return message.get("bytes", b"")
    
    async def iter_text(self) -> AsyncIterator[str]:
        """Iterate over text messages."""
        try:
            while True:
                yield await self.receive_text()
        except ConnectionError:
            pass
    
    async def iter_json(self) -> AsyncIterator[Any]:
        """Iterate over JSON messages."""
        async for text in self.iter_text():
            try:
                yield json.loads(text)
            except json.JSONDecodeError:
                pass


class WebSocketRoute:
    """Represents a WebSocket route."""
    
    def __init__(self, path: str, handler: Callable[..., Any]):
        """
        Initialize WebSocket route.
        
        Args:
            path: Route path pattern
            handler: Handler function
        """
        self.path = path
        self.handler = handler
        self.pattern = self._compile_pattern(path)
    
    def _compile_pattern(self, path: str) -> Any:
        """Compile path pattern to regex."""
        import re
        pattern = path.replace("{", "(?P<").replace("}", ">[^/]+)")
        return re.compile(f"^{pattern}$")
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Match path against pattern."""
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None


