import json
import re
import tempfile
from http.cookies import SimpleCookie
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs

from .files import UploadFile
from .interfaces import UserProtocol

class Request:
    """HTTP Request"""

    def __init__(self, scope: Dict[str, Any], body: bytes = b""):
        print(f"Creating Request with scope: {scope}")
        self.scope = scope
        self._body = body
        self._json = None
        self._form: Optional[Dict[str, Any]] = None
        self._files: Optional[Dict[str, UploadFile]] = None
        self._cookies: Optional[SimpleCookie] = None
        self.dependency_container = None
        self._user: Optional[UserProtocol] = None
        print(f"Request created: {self.method} {self.path}")

    @property
    def user(self) -> Optional[UserProtocol]:
        """Get authenticated user"""
        return self._user

    @user.setter
    def user(self, value: Optional[UserProtocol]):
        """Set authenticated user"""
        self._user = value

    @property
    def type(self) -> str:
        """Get request type"""
        return self.scope.get("type", "http")

    @property
    def method(self) -> str:
        """Request method"""
        method = self.scope.get("method", "GET")
        print(f"Request method: {method}")
        return method

    @property
    def path(self) -> str:
        """Request path"""
        path = self.scope.get("path", "/")
        print(f"Request path: {path}")
        return path

    @property
    def query_params(self) -> Dict[str, List[str]]:
        """Query parameters"""
        query_string = self.scope.get("query_string", b"").decode()
        return parse_qs(query_string)

    @property
    def headers(self) -> Dict[bytes, bytes]:
        """Request headers"""
        return {k: v for k, v in self.scope.get("headers", [])}

    @property
    def path_params(self) -> Dict[str, str]:
        """Path parameters"""
        return self.scope.get("path_params", {})

    @property
    def cookies(self) -> SimpleCookie:
        """Request cookies"""
        if self._cookies is None:
            self._cookies = SimpleCookie()
            headers = dict(self.scope.get("headers", []))
            cookie_header = headers.get(b"cookie", b"").decode()
            if cookie_header:
                self._cookies.load(cookie_header)
        return self._cookies

    async def json(self) -> Optional[Dict[str, Any]]:
        """Get JSON body"""
        if self._json is None:
            try:
                self._json = json.loads(self._body)
            except json.JSONDecodeError:
                return None
        return self._json

    @property
    def body(self) -> bytes:
        """Get raw body"""
        return self._body

    @property
    def content_type(self) -> str:
        """Content type of the request"""
        headers = dict(self.scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode()
        return content_type.split(";")[0].strip()

    async def form(self) -> Dict[str, Any]:
        """Get form data"""
        if self._form is None:
            content_type = self.content_type
            if content_type == "application/x-www-form-urlencoded":
                form_data = parse_qs(self._body.decode())
                self._form = {
                    k: v[0] if len(v) == 1 else v for k, v in form_data.items()
                }
            elif content_type.startswith("multipart/form-data"):
                self._form, self._files = await self._parse_multipart()
            else:
                self._form = {}
        return self._form

    async def files(self) -> Dict[str, UploadFile]:
        """Get uploaded files"""
        if self._files is None:
            if self.content_type.startswith("multipart/form-data"):
                self._form, self._files = await self._parse_multipart()
            else:
                self._files = {}
        return self._files

    async def _parse_multipart(self) -> Tuple[Dict[str, Any], Dict[str, UploadFile]]:
        """Parse multipart/form-data"""
        form_data = {}
        files = {}

        # Get boundary from Content-Type
        content_type = self.headers.get(b"content-type", b"").decode()
        boundary_match = re.search(r"boundary=([^;]+)", content_type)
        if not boundary_match:
            return form_data, files

        boundary = boundary_match.group(1)
        parts = self._body.split(f"--{boundary}".encode())

        # Skip first and last parts (empty)
        for part in parts[1:-1]:
            # Skip initial \r\n
            part = part.strip(b"\r\n")
            if not part:
                continue

            # Split headers and content
            try:
                headers_raw, content = part.split(b"\r\n\r\n", 1)
            except ValueError:
                continue

            headers = self._parse_part_headers(headers_raw.decode())

            # Get field name
            content_disposition = headers.get("Content-Disposition", "")
            name_match = re.search(r'name="([^"]+)"', content_disposition)
            if not name_match:
                continue
            name = name_match.group(1)

            # Check if this is a file
            filename_match = re.search(r'filename="([^"]+)"', content_disposition)
            if filename_match:
                # This is a file
                filename = filename_match.group(1)
                content_type = headers.get("Content-Type", "application/octet-stream")

                # Create UploadFile
                upload_file = UploadFile(
                    filename=filename, content_type=content_type, headers=headers
                )
                await upload_file.write(content.strip(b"\r\n"))
                files[name] = upload_file
            else:
                # This is a regular form field
                value = content.strip(b"\r\n").decode()
                form_data[name] = value

        return form_data, files

    def _parse_part_headers(self, headers_raw: str) -> Dict[str, str]:
        """Parse part headers in multipart/form-data"""
        headers = {}
        for line in headers_raw.split("\r\n"):
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip()] = value.strip()
        return headers

    @property
    def client(self) -> tuple:
        """Get client information (host, port)"""
        return self.scope.get("client", ("", 0))

    @property
    def url(self) -> str:
        """Get full URL of the request"""
        scheme = self.scope.get("scheme", "http")
        server = self.scope.get("server", ("localhost", 8000))
        path = self.scope.get("path", "/")
        query_string = self.scope.get("query_string", b"").decode()

        url = f"{scheme}://{server[0]}:{server[1]}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        return url
