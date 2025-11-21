"""
Request class for handling HTTP requests.

This module provides the Request class that wraps ASGI scope and provides
convenient access to request data like headers, query parameters, body, etc.
"""

import json
import urllib.parse
from typing import Dict, Any, Optional, List
from collections.abc import Mapping


class Request:
    """
    HTTP request wrapper for ASGI applications.

    Provides convenient access to:
    - HTTP method and path
    - Headers
    - Query parameters
    - Path parameters
    - Request body (JSON, form-data, etc.)
    - Cookies
    - Client information
    """

    def __init__(
        self,
        scope: Dict[str, Any],
        receive: Any,
        _body: Optional[bytes] = None,
        _path_params: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Request from ASGI scope.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            _body: Pre-loaded body (for testing)
            _path_params: Path parameters extracted from route
        """
        self.scope = scope
        self.receive = receive
        self._body = _body
        self._path_params = _path_params or {}
        self._json: Optional[Dict[str, Any]] = None
        self._form: Optional[Dict[str, str]] = None

    @property
    def method(self) -> str:
        """Get HTTP method (GET, POST, etc.)."""
        return self.scope.get("method", "GET")

    @property
    def path(self) -> str:
        """Get request path."""
        return self.scope.get("path", "/")

    @property
    def url(self) -> str:
        """Get full URL including query string."""
        scheme = self.scope.get("scheme", "http")
        server = self.scope.get("server")
        if server:
            host, port = server
            if (scheme == "http" and port != 80) or (scheme == "https" and port != 443):
                host = f"{host}:{port}"
        else:
            host = self.headers.get("host", "localhost")

        path = self.path
        query_string = self.scope.get("query_string", b"").decode()
        if query_string:
            path = f"{path}?{query_string}"

        return f"{scheme}://{host}{path}"

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers as dictionary (case-insensitive keys)."""
        if not hasattr(self, "_headers"):
            headers = {}
            for key, value in self.scope.get("headers", []):
                key_str = key.decode().lower()
                value_str = value.decode()
                headers[key_str] = value_str
            self._headers = headers
        return self._headers

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get header value by name (case-insensitive).

        Args:
            name: Header name
            default: Default value if header not found

        Returns:
            Header value or default
        """
        return self.headers.get(name.lower(), default)

    @property
    def query_params(self) -> Dict[str, List[str]]:
        """Get query parameters as dictionary."""
        if not hasattr(self, "_query_params"):
            query_string = self.scope.get("query_string", b"").decode()
            params: Dict[str, List[str]] = {}

            if query_string:
                parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)
                params = {k: v for k, v in parsed.items()}

            self._query_params = params
        return self._query_params

    def get_query_param(
        self, name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get single query parameter value.

        Args:
            name: Parameter name
            default: Default value if parameter not found

        Returns:
            First value of parameter or default
        """
        values = self.query_params.get(name, [])
        return values[0] if values else default

    @property
    def path_params(self) -> Dict[str, Any]:
        """Get path parameters extracted from route."""
        return self._path_params

    def get_path_param(self, name: str, default: Optional[Any] = None) -> Any:
        """
        Get path parameter value.

        Args:
            name: Parameter name
            default: Default value if parameter not found

        Returns:
            Parameter value or default
        """
        return self.path_params.get(name, default)

    @property
    def client(self) -> Optional[tuple]:
        """Get client address (host, port)."""
        return self.scope.get("client")

    @property
    def cookies(self) -> Dict[str, str]:
        """Get cookies as dictionary."""
        if not hasattr(self, "_cookies"):
            cookies: Dict[str, str] = {}
            cookie_header = self.get_header("cookie")

            if cookie_header:
                for cookie in cookie_header.split(";"):
                    cookie = cookie.strip()
                    if "=" in cookie:
                        key, value = cookie.split("=", 1)
                        cookies[key.strip()] = value.strip()

            self._cookies = cookies
        return self._cookies

    def get_cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get cookie value by name.

        Args:
            name: Cookie name
            default: Default value if cookie not found

        Returns:
            Cookie value or default
        """
        return self.cookies.get(name, default)

    async def body(self) -> bytes:
        """
        Get request body as bytes.

        Returns:
            Request body bytes
        """
        if self._body is not None:
            return self._body

        body = b""
        more_body = True

        while more_body:
            message = await self.receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        self._body = body
        return body

    async def json(self) -> Dict[str, Any]:
        """
        Parse request body as JSON.

        Returns:
            Parsed JSON as dictionary (empty dict if body is empty or invalid)

        Raises:
            ValueError: If body is not valid JSON (only if body is not empty)
        """
        if self._json is not None:
            return self._json

        body = await self.body()
        if not body:
            self._json = {}
            return self._json

        # Try to decode body
        try:
            body_str = body.decode()
        except UnicodeDecodeError:
            self._json = {}
            return self._json

        # If body is empty string or whitespace, return empty dict
        if not body_str.strip():
            self._json = {}
            return self._json

        try:
            self._json = json.loads(body_str)
        except json.JSONDecodeError as e:
            # If JSON is invalid, raise error only if body is not empty
            raise ValueError(f"Invalid JSON: {e}") from e

        return self._json

    async def form(self) -> Dict[str, str]:
        """
        Parse request body as form data.

        Returns:
            Parsed form data as dictionary
        """
        if self._form is not None:
            return self._form

        body = await self.body()
        if not body:
            self._form = {}
            return self._form

        try:
            form_data = urllib.parse.parse_qs(body.decode(), keep_blank_values=True)
            self._form = {k: v[0] if v else "" for k, v in form_data.items()}
        except Exception:
            self._form = {}

        return self._form

    @property
    def content_type(self) -> Optional[str]:
        """Get Content-Type header value."""
        return self.get_header("content-type")

    def is_json(self) -> bool:
        """Check if request has JSON content type."""
        content_type = self.content_type
        if not content_type:
            return False
        return "application/json" in content_type.lower()

    def is_form(self) -> bool:
        """Check if request has form content type."""
        content_type = self.content_type
        if not content_type:
            return False
        return "application/x-www-form-urlencoded" in content_type.lower()

    def is_multipart(self) -> bool:
        """Check if request has multipart content type."""
        content_type = self.content_type
        if not content_type:
            return False
        return "multipart/form-data" in content_type.lower()
