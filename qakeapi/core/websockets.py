import json
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Optional, Union


class WebSocketState(Enum):
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class WebSocket:
    def __init__(self, scope: Dict, receive: Any, send: Any):
        self.scope = scope
        self.receive = receive
        self.send = send
        self.state = WebSocketState.CONNECTING
        self._iter = None
        self.client = scope.get("client", None)

    async def accept(self, subprotocol: Optional[str] = None) -> None:
        """Accept the WebSocket connection"""
        if self.state != WebSocketState.CONNECTING:
            raise RuntimeError("WebSocket is not in CONNECTING state")

        await self.send({"type": "websocket.accept", "subprotocol": subprotocol})
        self.state = WebSocketState.CONNECTED

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        """Close the WebSocket connection"""
        if self.state == WebSocketState.DISCONNECTED:
            raise RuntimeError("WebSocket is already disconnected")

        await self.send({"type": "websocket.close", "code": code, "reason": reason})
        self.state = WebSocketState.DISCONNECTED

    async def send_text(self, data: str) -> None:
        """Send text data"""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "text": data})

    async def send_json(self, data: Any) -> None:
        """Send JSON data"""
        await self.send_text(json.dumps(data))

    async def send_bytes(self, data: bytes) -> None:
        """Send binary data"""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "bytes": data})

    async def send_ping(self, data: bytes = b"") -> None:
        """Send a ping frame"""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "bytes": data, "ping": True})

    async def send_pong(self, data: bytes = b"") -> None:
        """Send a pong frame"""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "bytes": data, "pong": True})

    async def receive_text(self) -> str:
        """Receive text data"""
        message = await self.receive()
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise RuntimeError("WebSocket disconnected")
        return message.get("text", "")

    async def receive_json(self) -> Any:
        """Receive JSON data"""
        data = await self.receive_text()
        return json.loads(data)

    async def receive_bytes(self) -> bytes:
        """Receive binary data"""
        message = await self.receive()
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise RuntimeError("WebSocket disconnected")
        return message.get("bytes", b"")

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate over incoming messages"""
        while self.state == WebSocketState.CONNECTED:
            message = await self.receive()
            if message["type"] == "websocket.disconnect":
                self.state = WebSocketState.DISCONNECTED
                break
            if "text" in message:
                yield message["text"]
            elif "bytes" in message:
                yield message["bytes"]


class WebSocketMiddleware:
    def __init__(self, app: Any, handler: Callable):
        self.app = app
        self.handler = handler

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope["type"] == "websocket":
            websocket = WebSocket(scope, receive, send)
            await self.handler(websocket)
        else:
            await self.app(scope, receive, send)
