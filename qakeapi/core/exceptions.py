"""
HTTP Exceptions for QakeAPI.

Provides exception classes for HTTP error responses.
"""

from typing import Any, Dict, Optional


class HTTPException(Exception):
    """Base HTTP exception."""
    
    def __init__(self, status_code: int, detail: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize HTTP exception.
        
        Args:
            status_code: HTTP status code
            detail: Error detail message
            headers: Optional headers to include in response
        """
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(detail)


class ValidationError(HTTPException):
    """Validation error (400 Bad Request)."""
    
    def __init__(self, detail: str, errors: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            detail: Error message
            errors: Dictionary of field errors
        """
        self.errors = errors
        super().__init__(400, detail)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {"error": self.detail}
        if self.errors:
            result["errors"] = self.errors
        return result


class NotFoundError(HTTPException):
    """Not found error (404 Not Found)."""
    
    def __init__(self, detail: str = "Not Found"):
        super().__init__(404, detail)


class UnauthorizedError(HTTPException):
    """Unauthorized error (401 Unauthorized)."""
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(401, detail)


class ForbiddenError(HTTPException):
    """Forbidden error (403 Forbidden)."""
    
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)


class InternalServerError(HTTPException):
    """Internal server error (500 Internal Server Error)."""
    
    def __init__(self, detail: str = "Internal Server Error"):
        super().__init__(500, detail)


class PayloadTooLargeError(HTTPException):
    """Payload too large error (413 Payload Too Large)."""
    
    def __init__(self, detail: str = "Payload Too Large"):
        super().__init__(413, detail)
