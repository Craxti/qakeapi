"""
WebSocket support for QakeAPI
"""
import json
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .exceptions import WebSocketException


class WebSocketState(Enum):
    """WebSocket connection states"""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocket:
    """Class for working with WebSocket connections"""

    def __init__(
        self, scope: Dict[str, Any], receive: callable, send: callable
    ) -> None:
        self._scope = scope
        self._receive = receive
        self._send = send
        self._state = WebSocketState.CONNECTING
        self._accepted = False
        self._closed = False

    @property
    def url(self) -> str:
        """WebSocket connection URL"""
        scheme = "ws" if self._scope.get("scheme") == "http" else "wss"
        server = self._scope.get("server", ("localhost", 80))
        path = self._scope.get("path", "/")
        query_string = self._scope.get("query_string", b"").decode()

        url = f"{scheme}://{server[0]}"
        if (scheme == "ws" and server[1] != 80) or (
            scheme == "wss" and server[1] != 443
        ):
            url += f":{server[1]}"
        url += path
        if query_string:
            url += f"?{query_string}"
        return url

    @property
    def path(self) -> str:
        """WebSocket connection path"""
        return self._scope.get("path", "/")

    @property
    def query_string(self) -> str:
        """WebSocket connection query string"""
        return self._scope.get("query_string", b"").decode()

    @property
    def headers(self) -> Dict[str, str]:
        """WebSocket connection headers"""
        headers = {}
        for name, value in self._scope.get("headers", []):
            headers[name.decode().lower()] = value.decode()
        return headers

    @property
    def client(self) -> Optional[tuple]:
        """Client information (IP, port)"""
        return self._scope.get("client")

    @property
    def state(self) -> WebSocketState:
        """Current connection state"""
        return self._state

    async def accept(
        self,
        subprotocol: Optional[str] = None,
        headers: Optional[List[tuple]] = None,
    ) -> None:
        """
        Accept WebSocket connection

        Args:
            subprotocol: Selected subprotocol
            headers: Additional headers
        """
        if self._accepted:
            raise WebSocketException(1002, "WebSocket already accepted")

        message = {
            "type": "websocket.accept",
        }

        if subprotocol:
            message["subprotocol"] = subprotocol

        if headers:
            message["headers"] = headers

        await self._send(message)
        self._accepted = True
        self._state = WebSocketState.CONNECTED

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """
        Close WebSocket connection

        Args:
            code: Close code
            reason: Close reason
        """
        if self._closed:
            return

        await self._send(
            {
                "type": "websocket.close",
                "code": code,
                "reason": reason,
            }
        )

        self._closed = True
        self._state = WebSocketState.DISCONNECTED

    async def send_text(self, data: str) -> None:
        """
        Send text message

        Args:
            data: Text data
        """
        if not self._accepted:
            raise WebSocketException(1002, "WebSocket not accepted")

        if self._closed:
            raise WebSocketException(1000, "WebSocket connection closed")

        await self._send(
            {
                "type": "websocket.send",
                "text": data,
            }
        )

    async def send_bytes(self, data: bytes) -> None:
        """
        Send binary message

        Args:
            data: Binary data
        """
        if not self._accepted:
            raise WebSocketException(1002, "WebSocket not accepted")

        if self._closed:
            raise WebSocketException(1000, "WebSocket connection closed")

        await self._send(
            {
                "type": "websocket.send",
                "bytes": data,
            }
        )

    async def send_json(self, data: Any, **json_kwargs: Any) -> None:
        """
        Send JSON message

        Args:
            data: Data for JSON serialization
            **json_kwargs: Additional parameters for json.dumps
        """
        json_data = json.dumps(data, ensure_ascii=False, **json_kwargs)
        await self.send_text(json_data)

    async def receive(self) -> Dict[str, Any]:
        """
        Receive message from client

        Returns:
            Dictionary with message data
        """
        message = await self._receive()

        if message["type"] == "websocket.connect":
            self._state = WebSocketState.CONNECTING
        elif message["type"] == "websocket.disconnect":
            self._state = WebSocketState.DISCONNECTED
            self._closed = True

        return message

    async def receive_text(self) -> str:
        """
        Receive text message

        Returns:
            Text data
        """
        message = await self.receive()

        if message["type"] == "websocket.receive":
            if "text" in message:
                return message["text"]
            else:
                raise WebSocketException(1003, "Expected text message")
        elif message["type"] == "websocket.disconnect":
            raise WebSocketException(1000, "WebSocket disconnected")
        else:
            raise WebSocketException(
                1002, f"Unexpected message type: {message['type']}"
            )

    async def receive_bytes(self) -> bytes:
        """
        Receive binary message

        Returns:
            Binary data
        """
        message = await self.receive()

        if message["type"] == "websocket.receive":
            if "bytes" in message:
                return message["bytes"]
            else:
                raise WebSocketException(1003, "Expected bytes message")
        elif message["type"] == "websocket.disconnect":
            raise WebSocketException(1000, "WebSocket disconnected")
        else:
            raise WebSocketException(
                1002, f"Unexpected message type: {message['type']}"
            )

    async def receive_json(self, **json_kwargs: Any) -> Any:
        """
        Receive JSON message

        Args:
            **json_kwargs: Additional parameters for json.loads

        Returns:
            Deserialized data
        """
        text_data = await self.receive_text()
        try:
            return json.loads(text_data, **json_kwargs)
        except json.JSONDecodeError as e:
            raise WebSocketException(1003, f"Invalid JSON: {str(e)}")

    async def iter_text(self):
        """
        Iterator for receiving text messages
        """
        try:
            while True:
                yield await self.receive_text()
        except WebSocketException:
            pass

    async def iter_bytes(self):
        """
        Iterator for receiving binary messages
        """
        try:
            while True:
                yield await self.receive_bytes()
        except WebSocketException:
            pass

    async def iter_json(self, **json_kwargs: Any):
        """
        Iterator for receiving JSON messages
        """
        try:
            while True:
                yield await self.receive_json(**json_kwargs)
        except WebSocketException:
            pass

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get header by name"""
        return self.headers.get(name.lower(), default)

    def get_query_param(
        self, name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get query parameter by name"""
        from urllib.parse import parse_qs

        if not self.query_string:
            return default

        parsed = parse_qs(self.query_string)
        values = parsed.get(name, [])
        return values[0] if values else default
