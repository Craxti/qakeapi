import json
from http.cookies import SimpleCookie
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple, Union


class Response:
    """HTTP Response"""

    def __init__(
        self,
        content: Union[str, bytes, dict, AsyncIterable[bytes]],
        status_code: int = 200,
        headers: Optional[List[Tuple[bytes, bytes]]] = None,
        media_type: Optional[str] = None,
        is_stream: bool = False,
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or []
        self.media_type = media_type
        self.is_stream = is_stream
        self._cookies = SimpleCookie()

    @property
    def status(self) -> int:
        """Для совместимости с ASGI"""
        return self.status_code

    @property
    async def body(self) -> bytes:
        """Get response body as bytes"""
        if self.is_stream:
            raise RuntimeError("Cannot get body of streaming response")
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode()
        elif isinstance(self.content, dict):
            return json.dumps(self.content).encode()
        else:
            return b""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to ASGI response dict"""
        if isinstance(self.content, dict):
            body = json.dumps(self.content).encode()
            if not any(h[0] == b"content-type" for h in self.headers):
                self.headers.append((b"content-type", b"application/json"))
        elif isinstance(self.content, str):
            body = self.content.encode()
            if not any(h[0] == b"content-type" for h in self.headers):
                self.headers.append((b"content-type", b"text/plain"))
        else:
            body = self.content

        return {"status": self.status_code, "headers": self.headers_list, "body": body}

    @property
    def headers_list(self) -> List[Tuple[bytes, bytes]]:
        """Get response headers"""
        headers = list(self.headers)

        # Add Content-Type if not set
        if not any(h[0] == b"content-type" for h in headers):
            media_type = self.media_type or self._get_media_type()
            headers.append((b"content-type", media_type.encode()))

        # Add cookie headers
        for cookie in self._cookies.values():
            headers.append((b"set-cookie", cookie.OutputString().encode()))

        # Add transfer-encoding for streaming responses
        if self.is_stream:
            headers.append((b"transfer-encoding", b"chunked"))

        return headers

    def _get_media_type(self) -> str:
        """Get content type based on content"""
        if self.is_stream:
            return self.media_type or "application/octet-stream"
        elif isinstance(self.content, bytes):
            return "application/octet-stream"
        elif isinstance(self.content, str):
            return "text/plain"
        else:
            return "application/json"

    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: Optional[int] = None,
        expires: Optional[int] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str = "lax",
    ) -> None:
        """Set response cookie"""
        self._cookies[key] = value
        if max_age is not None:
            self._cookies[key]["max-age"] = max_age
        if expires is not None:
            self._cookies[key]["expires"] = expires
        if path is not None:
            self._cookies[key]["path"] = path
        if domain is not None:
            self._cookies[key]["domain"] = domain
        if secure:
            self._cookies[key]["secure"] = secure
        if httponly:
            self._cookies[key]["httponly"] = httponly
        if samesite is not None:
            self._cookies[key]["samesite"] = samesite

    def delete_cookie(
        self, key: str, path: str = "/", domain: Optional[str] = None
    ) -> None:
        """Delete response cookie"""
        self.set_cookie(key, "", max_age=0, path=path, domain=domain)

    @classmethod
    def json(
        cls,
        content: dict,
        status_code: int = 200,
        headers: Optional[Union[Dict[str, str], List[Tuple[bytes, bytes]]]] = None
    ) -> "Response":
        """Create JSON response"""
        headers_list = []
        if headers:
            if isinstance(headers, dict):
                headers_list.extend((k.encode(), v.encode()) for k, v in headers.items())
            else:
                headers_list.extend(headers)
        
        headers_list.append((b"content-type", b"application/json"))
        return cls(
            json.dumps(content).encode(),
            status_code=status_code,
            headers=headers_list
        )

    @classmethod
    def text(
        cls,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> "Response":
        """Create text response"""
        headers_list = []
        if headers:
            headers_list.extend((k.encode(), v.encode()) for k, v in headers.items())
        return cls(
            content,
            status_code=status_code,
            headers=headers_list,
            media_type="text/plain"
        )

    @classmethod
    def html(
        cls,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> "Response":
        """Create HTML response"""
        headers_list = [(b"content-type", b"text/html; charset=utf-8")]
        if headers:
            headers_list.extend((k.encode(), v.encode()) for k, v in headers.items())
        return cls(
            content=content,
            status_code=status_code,
            headers=headers_list
        )

    @classmethod
    def redirect(
        cls,
        url: str,
        status_code: int = 302,
        headers: Optional[Dict[str, str]] = None
    ) -> "Response":
        """Create redirect response"""
        headers_list = [(b"location", url.encode())]
        if headers:
            headers_list.extend((k.encode(), v.encode()) for k, v in headers.items())
        return cls(b"", status_code=status_code, headers=headers_list)

    @classmethod
    def stream(
        cls,
        content: AsyncIterable[bytes],
        status_code: int = 200,
        media_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> "Response":
        """Create streaming response"""
        headers_list = []
        if headers:
            headers_list.extend((k.encode(), v.encode()) for k, v in headers.items())
        return cls(
            content,
            status_code=status_code,
            headers=headers_list,
            media_type=media_type,
            is_stream=True,
        )

    @property
    def headers_dict(self) -> Dict[str, str]:
        """Get response headers as dict"""
        return {k.decode(): v.decode() for k, v in self.headers_list}

    async def __call__(self, send) -> None:
        """Send response via ASGI"""
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers_list,
            }
        )

        if self.is_stream:
            async for chunk in self.content:
                await send(
                    {"type": "http.response.body", "body": chunk, "more_body": True}
                )
            await send({"type": "http.response.body", "body": b"", "more_body": False})
        else:
            body = await self.body
            await send({"type": "http.response.body", "body": body})


class JSONResponse(Response):
    """JSON Response"""
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[List[Tuple[bytes, bytes]]] = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="application/json"
        )

    @property
    async def body(self) -> bytes:
        return json.dumps(self.content).encode()
