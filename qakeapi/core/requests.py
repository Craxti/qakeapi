from typing import Dict, Any, Optional, List, Union
from urllib.parse import parse_qs
import json
from http.cookies import SimpleCookie
import re
import tempfile
from .files import UploadFile

class Request:
    """HTTP Request"""
    
    def __init__(self, scope: Dict[str, Any], body: bytes = b""):
        self.scope = scope
        self._body = body
        self._json = None
        self._form: Optional[Dict[str, Any]] = None
        self._files: Optional[Dict[str, UploadFile]] = None
        self._cookies: Optional[SimpleCookie] = None
        
    @property
    def method(self) -> str:
        """Request method"""
        return self.scope["method"]
        
    @property
    def path(self) -> str:
        """Request path"""
        return self.scope["path"]
        
    @property
    def query_params(self) -> Dict[str, list]:
        """Query parameters"""
        return parse_qs(self.scope.get("query_string", b"").decode())
        
    @property
    def headers(self) -> Dict[str, str]:
        """Request headers"""
        return dict(self.scope.get("headers", []))
        
    @property
    def path_params(self) -> Dict[str, str]:
        """Path parameters"""
        return self.scope.get("path_params", {})
        
    @property
    def cookies(self) -> SimpleCookie:
        """Cookies of the request"""
        if self._cookies is None:
            self._cookies = SimpleCookie()
            cookie_header = self.headers.get("cookie", "")
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
        
    async def body(self) -> bytes:
        """Get raw body"""
        return self._body
        
    @property
    def content_type(self) -> str:
        """Content-Type of the request"""
        content_type = self.headers.get("content-type", "")
        return content_type.split(";")[0].strip()
        
    async def form(self) -> Dict[str, Any]:
        """Get form body"""
        if self._form is None:
            content_type = self.content_type
            if content_type == "application/x-www-form-urlencoded":
                self._form = parse_qs(self._body.decode())
            elif content_type == "multipart/form-data":
                self._form, self._files = await self._parse_multipart()
            else:
                self._form = {}
        return self._form
        
    async def files(self) -> Dict[str, UploadFile]:
        """Get uploaded files"""
        if self._files is None:
            if self.content_type == "multipart/form-data":
                self._form, self._files = await self._parse_multipart()
            else:
                self._files = {}
        return self._files
        
    async def _parse_multipart(self) -> tuple[Dict[str, Any], Dict[str, UploadFile]]:
        """Parse multipart/form-data"""
        form_data = {}
        files = {}
        
        # Get boundary from Content-Type
        content_type = self.headers.get("content-type", "")
        boundary_match = re.search(r"boundary=([^;]+)", content_type)
        if not boundary_match:
            return form_data, files
            
        boundary = boundary_match.group(1)
        parts = self._body.split(f"--{boundary}".encode())
        
        # Skip the first and last parts (empty)
        for part in parts[1:-1]:
            # Skip initial \r\n
            part = part.strip(b"\r\n")
            
            # Split headers and content
            headers_raw, content = part.split(b"\r\n\r\n", 1)
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
                    filename=filename,
                    content_type=content_type,
                    headers=headers
                )
                await upload_file.write(content)
                files[name] = upload_file
            else:
                # This is a regular form field
                value = content.decode().strip()
                if name in form_data:
                    if isinstance(form_data[name], list):
                        form_data[name].append(value)
                    else:
                        form_data[name] = [form_data[name], value]
                else:
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