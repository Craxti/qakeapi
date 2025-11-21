"""
Response classes for HTTP responses.

This module provides various response classes for different content types:
- Response: Base response class
- JSONResponse: For JSON responses
- HTMLResponse: For HTML responses
- TextResponse: For plain text responses
- RedirectResponse: For redirects
- FileResponse: For file downloads
"""

import json
from typing import Any, Dict, Optional, Union
from http import HTTPStatus


class Response:
    """
    Base HTTP response class.

    This is the base class for all HTTP responses in the framework.
    """

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize response.

        Args:
            content: Response content
            status_code: HTTP status code
            headers: Additional headers
            media_type: Content-Type media type
            cookies: Cookies to set
        """
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = media_type
        self.cookies = cookies or {}

        # Set default Content-Type if not provided
        if media_type and "content-type" not in self.headers:
            self.headers["content-type"] = media_type

    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ):
        """
        Set a cookie in the response.

        Args:
            key: Cookie name
            value: Cookie value
            max_age: Max age in seconds
            expires: Expiration date string
            path: Cookie path
            domain: Cookie domain
            secure: Secure flag
            httponly: HttpOnly flag
            samesite: SameSite attribute (Strict, Lax, None)
        """
        cookie_parts = [f"{key}={value}"]

        if path:
            cookie_parts.append(f"Path={path}")
        if domain:
            cookie_parts.append(f"Domain={domain}")
        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        if expires:
            cookie_parts.append(f"Expires={expires}")
        if secure:
            cookie_parts.append("Secure")
        if httponly:
            cookie_parts.append("HttpOnly")
        if samesite:
            cookie_parts.append(f"SameSite={samesite}")

        cookie_string = "; ".join(cookie_parts)

        # Store in cookies dict and also set Set-Cookie header
        self.cookies[key] = cookie_string
        if "set-cookie" not in self.headers:
            self.headers["set-cookie"] = cookie_string
        else:
            # Multiple cookies - append
            existing = self.headers.get("set-cookie", "")
            if isinstance(existing, str):
                self.headers["set-cookie"] = [existing, cookie_string]
            else:
                self.headers["set-cookie"].append(cookie_string)

    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: Optional[str] = None,
    ):
        """
        Delete a cookie by setting it to expire.

        Args:
            key: Cookie name
            path: Cookie path
            domain: Cookie domain
        """
        self.set_cookie(key, "", max_age=0, path=path, domain=domain)

    def render(self) -> bytes:
        """
        Render response content to bytes.

        Returns:
            Response body as bytes
        """
        if self.content is None:
            return b""

        if isinstance(self.content, bytes):
            return self.content

        if isinstance(self.content, str):
            return self.content.encode("utf-8")

        return str(self.content).encode("utf-8")

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any):
        """
        ASGI application interface.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        body = self.render()

        # Prepare headers
        headers = []
        for key, value in self.headers.items():
            if isinstance(value, list):
                for v in value:
                    headers.append([key.encode(), str(v).encode()])
            else:
                headers.append([key.encode(), str(value).encode()])

        # Add Set-Cookie headers from cookies
        for cookie_string in self.cookies.values():
            if isinstance(cookie_string, str):
                headers.append([b"set-cookie", cookie_string.encode()])

        # Send response
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": headers,
            }
        )

        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


class JSONResponse(Response):
    """Response class for JSON content."""

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize JSON response.

        Args:
            content: Data to serialize as JSON
            status_code: HTTP status code
            headers: Additional headers
            cookies: Cookies to set
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="application/json",
            cookies=cookies,
        )

    def render(self) -> bytes:
        """Render JSON content to bytes."""
        if self.content is None:
            return b"{}"

        try:
            return json.dumps(self.content, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot serialize to JSON: {e}") from e


class HTMLResponse(Response):
    """Response class for HTML content."""

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize HTML response.

        Args:
            content: HTML content string
            status_code: HTTP status code
            headers: Additional headers
            cookies: Cookies to set
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/html; charset=utf-8",
            cookies=cookies,
        )


class TextResponse(Response):
    """Response class for plain text content."""

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize text response.

        Args:
            content: Text content string
            status_code: HTTP status code
            headers: Additional headers
            cookies: Cookies to set
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/plain; charset=utf-8",
            cookies=cookies,
        )


class RedirectResponse(Response):
    """Response class for HTTP redirects."""

    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize redirect response.

        Args:
            url: Redirect URL
            status_code: Redirect status code (301, 302, 303, 307, 308)
            headers: Additional headers
        """
        if status_code not in (301, 302, 303, 307, 308):
            raise ValueError(f"Invalid redirect status code: {status_code}")

        redirect_headers = headers or {}
        redirect_headers["location"] = url

        super().__init__(
            content="",
            status_code=status_code,
            headers=redirect_headers,
        )


class FileResponse(Response):
    """Response class for file downloads."""

    def __init__(
        self,
        path: str,
        filename: Optional[str] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ):
        """
        Initialize file response.

        Args:
            path: File path
            filename: Optional filename for download
            status_code: HTTP status code
            headers: Additional headers
            media_type: Content-Type (auto-detected if not provided)
        """
        self.file_path = path
        self.filename = filename

        # Auto-detect media type if not provided
        if not media_type:
            import mimetypes

            media_type, _ = mimetypes.guess_type(path)
            if not media_type:
                media_type = "application/octet-stream"

        file_headers = headers or {}

        if filename:
            file_headers["content-disposition"] = f'attachment; filename="{filename}"'

        super().__init__(
            content=None,  # Will be loaded from file
            status_code=status_code,
            headers=file_headers,
            media_type=media_type,
        )

    def render(self) -> bytes:
        """Read and render file content."""
        try:
            with open(self.file_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.file_path}")
        except IOError as e:
            raise IOError(f"Error reading file: {e}") from e
