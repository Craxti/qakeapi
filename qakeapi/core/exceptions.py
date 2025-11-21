"""
Exception classes for the framework.

This module provides custom exception classes for HTTP errors and framework errors.
"""

from typing import Any, Dict, List, Optional


class HTTPException(Exception):
    """
    Base HTTP exception class.

    Used for raising HTTP errors with status codes and error messages.
    """

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize HTTP exception.

        Args:
            status_code: HTTP status code
            detail: Error detail message or data
            headers: Optional HTTP headers
        """
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(self.detail)


class FrameworkException(Exception):
    """
    Base framework exception class.

    Used for framework-level errors that are not HTTP-related.
    """

    def __init__(self, message: str):
        """
        Initialize framework exception.

        Args:
            message: Error message
        """
        self.message = message
        super().__init__(self.message)


# Common HTTP exceptions
class BadRequest(HTTPException):
    """400 Bad Request exception."""

    def __init__(self, detail: Any = "Bad Request"):
        super().__init__(400, detail)


class Unauthorized(HTTPException):
    """401 Unauthorized exception."""

    def __init__(self, detail: Any = "Unauthorized"):
        super().__init__(401, detail)


class Forbidden(HTTPException):
    """403 Forbidden exception."""

    def __init__(self, detail: Any = "Forbidden"):
        super().__init__(403, detail)


class NotFound(HTTPException):
    """404 Not Found exception."""

    def __init__(self, detail: Any = "Not Found"):
        super().__init__(404, detail)


class MethodNotAllowed(HTTPException):
    """405 Method Not Allowed exception."""

    def __init__(self, detail: Any = "Method Not Allowed"):
        super().__init__(405, detail)


class Conflict(HTTPException):
    """409 Conflict exception."""

    def __init__(self, detail: Any = "Conflict"):
        super().__init__(409, detail)


class InternalServerError(HTTPException):
    """500 Internal Server Error exception."""

    def __init__(self, detail: Any = "Internal Server Error"):
        super().__init__(500, detail)


# Additional exceptions for compatibility
class ValidationException(HTTPException):
    """422 Unprocessable Entity exception for validation errors."""

    def __init__(
        self, detail: Any = "Validation Error", errors: Optional[List[str]] = None
    ):
        super().__init__(422, detail)
        self.errors = errors or []


class QakeAPIException(FrameworkException):
    """Alias for FrameworkException for backward compatibility."""

    pass


class AuthenticationException(HTTPException):
    """401 Unauthorized exception for authentication errors."""

    def __init__(self, detail: Any = "Authentication required", headers: Optional[Dict[str, str]] = None):
        super().__init__(401, detail, headers)


class AuthorizationException(HTTPException):
    """403 Forbidden exception for authorization errors."""

    def __init__(self, detail: Any = "Authorization required"):
        super().__init__(403, detail)
