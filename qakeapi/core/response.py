"""
HTTP Response handling.

This module provides response classes for different HTTP response types.
"""

from typing import Any, Dict, List, Optional


class Response:
    """
    Base HTTP Response class.
    
    All response types inherit from this class.
    """
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ):
        """
        Initialize response.
        
        Args:
            content: Response content
            status_code: HTTP status code
            headers: Response headers
            media_type: Media type (Content-Type)
        """
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = media_type
    
    async def __call__(self, send: Any) -> None:
        """ASGI interface - send response."""
        await self._send(send)
    
    async def _send(self, send: Any) -> None:
        """Internal method to send response."""
        headers = self._prepare_headers()
        
        # Send start response
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": headers,
        })
        
        # Send body
        body = self._get_body()
        await send({
            "type": "http.response.body",
            "body": body,
        })
    
    def _prepare_headers(self) -> List[tuple]:
        """Prepare headers for ASGI."""
        headers = []
        
        # Content-Type
        if self.media_type:
            headers.append((b"content-type", self.media_type.encode()))
        
        # Custom headers
        for key, value in self.headers.items():
            key_bytes = key.encode() if isinstance(key, str) else key
            value_bytes = value.encode() if isinstance(value, str) else value
            headers.append((key_bytes, value_bytes))
        
        return headers
    
    def _get_body(self) -> bytes:
        """Get response body as bytes."""
        if self.content is None:
            return b""
        if isinstance(self.content, bytes):
            return self.content
        if isinstance(self.content, str):
            return self.content.encode()
        return str(self.content).encode()


class JSONResponse(Response):
    """JSON response."""
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize JSON response."""
        import json
        
        json_content = json.dumps(content).encode() if content is not None else b"{}"
        super().__init__(
            content=json_content,
            status_code=status_code,
            headers=headers,
            media_type="application/json",
        )


class HTMLResponse(Response):
    """HTML response."""
    
    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize HTML response."""
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/html",
        )


class TextResponse(Response):
    """Plain text response."""
    
    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize text response."""
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/plain",
        )

