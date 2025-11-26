"""
HTTP Request handling.

This module provides the Request class for handling HTTP requests.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from .files import FileUpload, parse_multipart


class Request:
    """
    HTTP Request object.
    
    Represents an incoming HTTP request with all its components:
    - Method (GET, POST, etc.)
    - Path and query parameters
    - Headers
    - Body
    - Cookies
    """
    
    def __init__(self, scope: Dict[str, Any], receive: Any = None):
        """
        Initialize request from ASGI scope.
        
        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable (optional)
        """
        self.scope = scope
        self._receive = receive
        self._body: Optional[bytes] = None
        self._json: Optional[Any] = None
        self._form_data: Optional[Dict[str, Any]] = None
        self._multipart_data: Optional[Dict[str, Any]] = None
    
    @property
    def method(self) -> str:
        """HTTP method."""
        return self.scope.get("method", "GET")
    
    @property
    def path(self) -> str:
        """Request path."""
        return self.scope.get("path", "/")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Request headers as dictionary."""
        headers_dict = {}
        for key, value in self.scope.get("headers", []):
            key_str = key.decode() if isinstance(key, bytes) else key
            value_str = value.decode() if isinstance(value, bytes) else value
            headers_dict[key_str.lower()] = value_str
        return headers_dict
    
    @property
    def query_params(self) -> Dict[str, List[str]]:
        """Query parameters."""
        query_string = self.scope.get("query_string", b"").decode()
        if not query_string:
            return {}
        
        parsed = parse_qs(query_string, keep_blank_values=True)
        return {k: v for k, v in parsed.items()}
    
    def get_query_param(self, key: str, default: Any = None) -> Any:
        """Get single query parameter value."""
        values = self.query_params.get(key, [])
        return values[0] if values else default
    
    async def body(self) -> bytes:
        """Get request body as bytes."""
        if self._body is None:
            if self._receive is None:
                return b""
            
            self._body = b""
            more_body = True
            while more_body:
                message = await self._receive()
                self._body += message.get("body", b"")
                more_body = message.get("more_body", False)
        
        return self._body
    
    async def json(self, default: Any = None) -> Any:
        """
        Parse request body as JSON.
        
        Args:
            default: Default value if body is empty (default: None)
            
        Returns:
            Parsed JSON data or default value if body is empty
            
        Raises:
            ValueError: If JSON is invalid
        """
        if self._json is None:
            body = await self.body()
            if not body:
                # Return default instead of empty dict for better error handling
                return default
            try:
                self._json = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ValueError(f"Invalid JSON in request body: {str(e)}")
        
        return self._json
    
    async def form(self) -> Dict[str, Any]:
        """Parse request body as form data."""
        if self._form_data is None:
            # Simple form parsing - can be enhanced
            body = await self.body()
            self._form_data = {}
            if body:
                form_string = body.decode()
                for pair in form_string.split("&"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        self._form_data[key] = value
        
        return self._form_data
    
    async def files(self) -> Dict[str, FileUpload]:
        """
        Parse multipart/form-data and return uploaded files.
        
        Returns:
            Dictionary mapping field names to FileUpload objects
            
        Raises:
            ValueError: If request is not multipart/form-data
        """
        if self._multipart_data is None:
            content_type = self.headers.get("content-type", "")
            if not content_type.startswith("multipart/form-data"):
                return {}
            
            body = await self.body()
            self._multipart_data = parse_multipart(body, content_type)
        
        return self._multipart_data.get("files", {})
    
    async def form_and_files(self) -> Dict[str, Any]:
        """
        Parse multipart/form-data and return both form fields and files.
        
        Returns:
            Dictionary with 'fields' and 'files' keys
            
        Raises:
            ValueError: If request is not multipart/form-data
        """
        if self._multipart_data is None:
            content_type = self.headers.get("content-type", "")
            if not content_type.startswith("multipart/form-data"):
                return {"fields": {}, "files": {}}
            
            body = await self.body()
            self._multipart_data = parse_multipart(body, content_type)
        
        return self._multipart_data
    
    def get_file(self, field_name: str) -> Optional[FileUpload]:
        """
        Get uploaded file by field name (synchronous, requires files() to be called first).
        
        Args:
            field_name: Form field name
            
        Returns:
            FileUpload object or None if not found
        """
        if self._multipart_data is None:
            return None
        
        return self._multipart_data.get("files", {}).get(field_name)
    
    @property
    def client(self) -> Optional[tuple]:
        """Client address (host, port)."""
        return self.scope.get("client")
