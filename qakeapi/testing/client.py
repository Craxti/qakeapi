"""
Test client for testing QakeAPI applications.

This module provides test clients for HTTP and WebSocket testing.
"""

import asyncio
from typing import Any, Dict, Optional
from qakeapi.core.application import QakeAPI
from qakeapi.core.request import Request
from qakeapi.core.response import Response, JSONResponse


class TestClient:  # noqa: N801
    """
    Test client for HTTP requests.
    
    Allows testing ASGI applications without running a server.
    """
    
    def __init__(self, app: QakeAPI):
        """
        Initialize test client.
        
        Args:
            app: QakeAPI application instance
        """
        self.app = app
    
    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> "TestResponse":
        """
        Make HTTP request.
        
        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            params: Query parameters
            json: JSON body
            data: Raw body data
            cookies: Cookies
            
        Returns:
            TestResponse instance
        """
        # Build query string
        query_string = b""
        if params:
            import urllib.parse
            query_parts = []
            for key, value in params.items():
                if isinstance(value, list):
                    for v in value:
                        query_parts.append(f"{key}={urllib.parse.quote(str(v))}")
                else:
                    query_parts.append(f"{key}={urllib.parse.quote(str(value))}")
            query_string = "&".join(query_parts).encode()
        
        # Prepare headers
        headers_list = []
        if headers:
            for key, value in headers.items():
                headers_list.append((key.encode(), str(value).encode()))
        
        # Add cookies to headers
        if cookies:
            cookie_parts = [f"{k}={v}" for k, v in cookies.items()]
            headers_list.append((b"cookie", "; ".join(cookie_parts).encode()))
        
        # Prepare body
        body = b""
        if json:
            import json as json_lib
            body = json_lib.dumps(json).encode()
            headers_list.append((b"content-type", b"application/json"))
        elif data:
            body = data
        
        # Create ASGI scope
        scope = {
            "type": "http",
            "method": method.upper(),
            "path": path,
            "query_string": query_string,
            "headers": headers_list,
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
        }
        
        # Collect response
        response_data = {
            "status": None,
            "headers": {},
            "body": b"",
        }
        
        async def receive():
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
        
        async def send(message: Dict[str, Any]):
            if message["type"] == "http.response.start":
                response_data["status"] = message["status"]
                for key, value in message.get("headers", []):
                    key_str = key.decode().lower()
                    value_str = value.decode()
                    response_data["headers"][key_str] = value_str
            elif message["type"] == "http.response.body":
                response_data["body"] += message.get("body", b"")
        
        # Process request
        await self.app(scope, receive, send)
        
        return TestResponse(
            status_code=response_data["status"],
            headers=response_data["headers"],
            content=response_data["body"],
        )
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> "TestResponse":
        """Make GET request."""
        return asyncio.run(self.request("GET", path, headers, params, cookies=cookies))
    
    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> "TestResponse":
        """Make POST request."""
        return asyncio.run(
            self.request("POST", path, headers, params, json, data, cookies)
        )
    
    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> "TestResponse":
        """Make PUT request."""
        return asyncio.run(
            self.request("PUT", path, headers, None, json, data, cookies)
        )
    
    def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> "TestResponse":
        """Make DELETE request."""
        return asyncio.run(self.request("DELETE", path, headers, None, None, None, cookies))
    
    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> "TestResponse":
        """Make PATCH request."""
        return asyncio.run(
            self.request("PATCH", path, headers, None, json, data, cookies)
        )


class TestResponse:  # noqa: N801
    """Test response wrapper."""
    
    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        content: bytes,
    ):
        """
        Initialize test response.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            content: Response body
        """
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self._json: Optional[Dict[str, Any]] = None
    
    @property
    def text(self) -> str:
        """Get response as text."""
        return self.content.decode("utf-8")
    
    def json(self) -> Dict[str, Any]:
        """Get response as JSON."""
        if self._json is None:
            import json
            self._json = json.loads(self.text)
        return self._json
    
    def raise_for_status(self):
        """Raise exception if status code indicates error."""
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}: {self.text}")


class WebSocketTestClient:
    """
    Test client for WebSocket connections.
    """
    
    def __init__(self, app: QakeAPI):
        """
        Initialize WebSocket test client.
        
        Args:
            app: QakeAPI application instance
        """
        self.app = app
        self.messages_sent = []
        self.messages_received = []
    
    async def connect(self, path: str) -> "WebSocketTestSession":
        """
        Connect to WebSocket endpoint.
        
        Args:
            path: WebSocket path
            
        Returns:
            WebSocketTestSession instance
        """
        scope = {
            "type": "websocket",
            "path": path,
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
        
        messages_to_send = [
            {"type": "websocket.connect"},
        ]
        messages_received = []
        
        async def receive():
            if messages_to_send:
                return messages_to_send.pop(0)
            return {"type": "websocket.disconnect"}
        
        async def send(message: Dict[str, Any]):
            messages_received.append(message)
        
        # Start connection in background
        task = asyncio.create_task(self.app(scope, receive, send))
        
        # Wait a bit for connection
        await asyncio.sleep(0.01)
        
        return WebSocketTestSession(messages_to_send, messages_received, task)


class WebSocketTestSession:
    """WebSocket test session."""
    
    def __init__(
        self,
        messages_to_send: list,
        messages_received: list,
        task: asyncio.Task,
    ):
        """
        Initialize WebSocket test session.
        
        Args:
            messages_to_send: Queue of messages to send
            messages_received: List of received messages
            task: Background task
        """
        self.messages_to_send = messages_to_send
        self.messages_received = messages_received
        self.task = task
    
    def send_text(self, text: str):
        """Send text message."""
        self.messages_to_send.append({
            "type": "websocket.receive",
            "text": text,
        })
    
    def send_json(self, data: Dict[str, Any]):
        """Send JSON message."""
        import json
        self.send_text(json.dumps(data))
    
    def receive(self) -> Dict[str, Any]:
        """Receive message."""
        # Wait a bit for processing
        asyncio.run(asyncio.sleep(0.01))
        if self.messages_received:
            return self.messages_received.pop(0)
        return None
    
    def close(self):
        """Close connection."""
        self.messages_to_send.append({"type": "websocket.disconnect"})
        if not self.task.done():
            self.task.cancel()

