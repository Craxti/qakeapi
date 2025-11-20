"""
Exceptions for QakeAPI framework
"""
from typing import Any, Dict, Optional, Union


class QakeAPIException(Exception):
    """Base exception for QakeAPI"""
    
    def __init__(self, message: str = "Internal Server Error") -> None:
        self.message = message
        super().__init__(self.message)


class HTTPException(QakeAPIException):
    """HTTP exception with status code"""
    
    def __init__(
        self,
        status_code: int,
        detail: Union[str, Dict[str, Any]] = "Internal Server Error",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        
        message = f"HTTP {status_code}"
        if isinstance(detail, str):
            message += f": {detail}"
        
        super().__init__(message)


class ValidationException(HTTPException):
    """Data validation exception"""
    
    def __init__(
        self,
        detail: Union[str, Dict[str, Any]] = "Validation Error",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(422, detail, headers)


class AuthenticationException(HTTPException):
    """Authentication exception"""
    
    def __init__(
        self,
        detail: str = "Authentication required",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(401, detail, headers)


class AuthorizationException(HTTPException):
    """Authorization exception"""
    
    def __init__(
        self,
        detail: str = "Insufficient permissions",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(403, detail, headers)


class NotFoundException(HTTPException):
    """Not found exception"""
    
    def __init__(
        self,
        detail: str = "Not Found",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(404, detail, headers)


class MethodNotAllowedException(HTTPException):
    """Method not allowed exception"""
    
    def __init__(
        self,
        detail: str = "Method Not Allowed",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(405, detail, headers)


class RateLimitException(HTTPException):
    """Rate limit exceeded exception"""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(429, detail, headers)


class WebSocketException(QakeAPIException):
    """Exception for WebSocket connections"""
    
    def __init__(
        self,
        code: int = 1000,
        reason: str = "Connection closed",
    ) -> None:
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket {code}: {reason}")
