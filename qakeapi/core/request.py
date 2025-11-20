"""
Request class for QakeAPI
"""
import json
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from urllib.parse import parse_qs, unquote_plus
import asyncio

from ..core.exceptions import ValidationException


class Request:
    """Class for working with HTTP requests"""
    
    def __init__(self, scope: Dict[str, Any], receive: callable) -> None:
        self._scope = scope
        self._receive = receive
        self._body: Optional[bytes] = None
        self._json: Optional[Any] = None
        self._form: Optional[Dict[str, Any]] = None
        self._query_params: Optional[Dict[str, Union[str, List[str]]]] = None
        self._path_params: Dict[str, str] = {}
        self._cookies: Optional[Dict[str, str]] = None
        self._headers: Optional[Dict[str, str]] = None
    
    @property
    def scope(self) -> Dict[str, Any]:
        """ASGI scope"""
        return self._scope
        
    @property
    def method(self) -> str:
        """HTTP method of request"""
        return self._scope["method"]
    
    @property
    def url(self) -> str:
        """Full URL of request"""
        scheme = self._scope.get("scheme", "http")
        server = self._scope.get("server", ("localhost", 80))
        path = self._scope.get("path", "/")
        query_string = self._scope.get("query_string", b"").decode()
        
        url = f"{scheme}://{server[0]}"
        if (scheme == "http" and server[1] != 80) or (scheme == "https" and server[1] != 443):
            url += f":{server[1]}"
        url += path
        if query_string:
            url += f"?{query_string}"
        return url
    
    @property
    def path(self) -> str:
        """Request path"""
        return self._scope.get("path", "/")
    
    @property
    def client(self) -> Optional[tuple]:
        """Client information (host, port)"""
        return self._scope.get("client")
    
    @property
    def query_string(self) -> str:
        """Request query string"""
        return self._scope.get("query_string", b"").decode()
    
    @property
    def headers(self) -> Dict[str, str]:
        """Request headers"""
        if self._headers is None:
            self._headers = {}
            for name, value in self._scope.get("headers", []):
                self._headers[name.decode().lower()] = value.decode()
        return self._headers
    
    @property
    def cookies(self) -> Dict[str, str]:
        """Cookies from request"""
        if self._cookies is None:
            self._cookies = {}
            cookie_header = self.headers.get("cookie", "")
            if cookie_header:
                for chunk in cookie_header.split(";"):
                    if "=" in chunk:
                        key, value = chunk.strip().split("=", 1)
                        self._cookies[key] = unquote_plus(value)
        return self._cookies
    
    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        """Request query parameters"""
        if self._query_params is None:
            self._query_params = {}
            if self.query_string:
                parsed = parse_qs(self.query_string, keep_blank_values=True)
                for key, values in parsed.items():
                    if len(values) == 1:
                        self._query_params[key] = values[0]
                    else:
                        self._query_params[key] = values
        return self._query_params
    
    @property
    def path_params(self) -> Dict[str, str]:
        """Path parameters (set by router)"""
        return self._path_params
    
    def set_path_params(self, params: Dict[str, str]) -> None:
        """Set path parameters"""
        self._path_params = params
    
    
    @property
    def content_type(self) -> Optional[str]:
        """Content-Type header"""
        return self.headers.get("content-type")
    
    @property
    def content_length(self) -> Optional[int]:
        """Content-Length header"""
        length = self.headers.get("content-length")
        return int(length) if length else None
    
    async def body(self) -> bytes:
        """Get request body as bytes"""
        if self._body is None:
            body_parts = []
            while True:
                message = await self._receive()
                if message["type"] == "http.request":
                    body_parts.append(message.get("body", b""))
                    if not message.get("more_body", False):
                        break
                elif message["type"] == "http.disconnect":
                    break
            self._body = b"".join(body_parts)
        return self._body
    
    async def text(self) -> str:
        """Get request body as text"""
        body = await self.body()
        return body.decode("utf-8")
    
    async def json(self) -> Any:
        """Get request body as JSON"""
        if self._json is None:
            body = await self.body()
            if not body:
                return None
            try:
                self._json = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ValidationException(f"Invalid JSON: {str(e)}")
        return self._json
    
    async def form(self) -> Dict[str, Any]:
        """Get form data"""
        if self._form is None:
            content_type = self.content_type or ""
            if "application/x-www-form-urlencoded" in content_type:
                body = await self.text()
                self._form = {}
                if body:
                    parsed = parse_qs(body, keep_blank_values=True)
                    for key, values in parsed.items():
                        if len(values) == 1:
                            self._form[key] = values[0]
                        else:
                            self._form[key] = values
            elif "multipart/form-data" in content_type:
                # For multipart/form-data more complex processing is needed
                # For now return empty dictionary
                self._form = {}
            else:
                self._form = {}
        return self._form
    
    async def stream(self) -> AsyncGenerator[bytes, None]:
        """Stream request body"""
        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                yield message.get("body", b"")
                if not message.get("more_body", False):
                    break
            elif message["type"] == "http.disconnect":
                break
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get header by name"""
        return self.headers.get(name.lower(), default)
    
    def get_query_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get query parameter by name"""
        value = self.query_params.get(name, default)
        if isinstance(value, list):
            return value[0] if value else default
        return value
    
    def get_path_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get path parameter by name"""
        return self.path_params.get(name, default)
    
    def get_cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get cookie by name"""
        return self.cookies.get(name, default)
    
    def is_secure(self) -> bool:
        """Check if connection is secure (HTTPS)"""
        return self._scope.get("scheme") == "https"
    
    def is_ajax(self) -> bool:
        """Check if request is AJAX"""
        return self.get_header("x-requested-with", "").lower() == "xmlhttprequest"
    
    def accepts(self, content_type: str) -> bool:
        """Check if client accepts specified content-type"""
        accept_header = self.get_header("accept", "")
        return content_type in accept_header or "*/*" in accept_header
