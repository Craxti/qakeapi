"""XSS Protection Module.

This module provides XSS protection middleware and utilities for QakeAPI framework.
"""
from typing import Any, Dict, Optional, Union
import html
import re
from qakeapi.core.middleware import BaseMiddleware
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response

class XSSProtection:
    """XSS Protection utility class."""
    
    DANGEROUS_ATTRIBUTES = [
        'onabort', 'onblur', 'onchange', 'onclick', 'ondblclick', 'onerror', 'onfocus',
        'onkeydown', 'onkeypress', 'onkeyup', 'onload', 'onmousedown', 'onmousemove',
        'onmouseout', 'onmouseover', 'onmouseup', 'onreset', 'onresize', 'onselect',
        'onsubmit', 'onunload'
    ]
    
    @staticmethod
    def clean_html(value: str) -> str:
        """Escape HTML special characters."""
        return html.escape(value)
    
    @staticmethod
    def clean_javascript(value: str) -> str:
        """Remove potentially dangerous JavaScript."""
        # First, normalize the string
        value = value.lower()
        
        # Remove script tags and their contents
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove inline event handlers
        for attr in XSSProtection.DANGEROUS_ATTRIBUTES:
            value = re.sub(
                fr'\s*{attr}\s*=\s*(["\'])[^"\']*\1',
                ' data-removed=""',
                value,
                flags=re.IGNORECASE
            )
        
        # Remove dangerous protocols
        value = re.sub(r'javascript:', 'removed:', value, flags=re.IGNORECASE)
        value = re.sub(r'data:', 'removed:', value, flags=re.IGNORECASE)
        value = re.sub(r'vbscript:', 'removed:', value, flags=re.IGNORECASE)
        
        # Remove expression(...) CSS
        value = re.sub(r'expression\s*\([^)]*\)', 'removed()', value, flags=re.IGNORECASE)
        
        # Remove other potentially dangerous patterns
        dangerous_tags = [
            r'<!--.*?-->',  # Comments
            r'<!\[CDATA\[.*?\]\]>',  # CDATA
            r'<!DOCTYPE[^>]*>',  # DOCTYPE
            r'<base[^>]*>',  # base tag
            r'<link[^>]*>',  # link tag
            r'<meta[^>]*>',  # meta tag
            r'<object[^>]*>.*?</object>',  # object tag
            r'<embed[^>]*>',  # embed tag
            r'<applet[^>]*>.*?</applet>',  # applet tag
        ]
        
        for pattern in dangerous_tags:
            value = re.sub(pattern, '', value, flags=re.DOTALL | re.IGNORECASE)
        
        return value
    
    @classmethod
    def sanitize_value(cls, value: Any) -> Any:
        """Sanitize a single value."""
        if isinstance(value, str):
            value = cls.clean_javascript(value)
            value = cls.clean_html(value)
        return value
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values."""
        if not isinstance(data, dict):
            return data
        return {k: cls.sanitize_value(v) if isinstance(v, (str, int, float, bool))
                else cls.sanitize_dict(v) if isinstance(v, dict)
                else v for k, v in data.items()}

class XSSMiddleware(BaseMiddleware):
    """Middleware for XSS protection."""
    
    async def process_request(self, request: Request) -> Optional[Response]:
        """Process request data for XSS protection."""
        # Create new sanitized query params
        sanitized_params = XSSProtection.sanitize_dict(dict(request.query_params))
        request._query_params = sanitized_params
        
        # Sanitize form data if present
        if hasattr(request, 'form_data') and request.form_data:
            sanitized_form = XSSProtection.sanitize_dict(dict(request.form_data))
            request._form_data = sanitized_form
            
        # Sanitize JSON data if present
        if hasattr(request, 'json') and request.json:
            if isinstance(request.json, dict):
                request.json = XSSProtection.sanitize_dict(request.json)
            elif isinstance(request.json, str):
                request.json = XSSProtection.sanitize_value(request.json)
            
        return None
    
    async def process_response(self, response: Response) -> Response:
        """Process response data for XSS protection."""
        if hasattr(response, 'content') and isinstance(response.content, (str, bytes)):
            response._content = XSSProtection.sanitize_value(str(response.content))
        elif hasattr(response, 'content') and isinstance(response.content, dict):
            response._content = XSSProtection.sanitize_dict(response.content)
        return response 