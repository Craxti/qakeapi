"""
Tests for HTTP exceptions.
"""

import pytest
from qakeapi.core.exceptions import (
    HTTPException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    InternalServerError,
    PayloadTooLargeError
)


class TestHTTPException:
    """Tests for HTTPException base class."""
    
    def test_http_exception_creation(self):
        """Test creating HTTPException."""
        exc = HTTPException(404, "Not Found")
        assert exc.status_code == 404
        assert exc.detail == "Not Found"
        assert exc.headers == {}
    
    def test_http_exception_with_headers(self):
        """Test HTTPException with custom headers."""
        headers = {"X-Custom": "value"}
        exc = HTTPException(400, "Bad Request", headers=headers)
        assert exc.headers == headers
    
    def test_http_exception_str(self):
        """Test HTTPException string representation."""
        exc = HTTPException(404, "Not Found")
        assert str(exc) == "Not Found"


class TestValidationError:
    """Tests for ValidationError."""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        exc = ValidationError("Validation failed")
        assert exc.status_code == 400
        assert exc.detail == "Validation failed"
        assert exc.errors is None
    
    def test_validation_error_with_errors(self):
        """Test ValidationError with field errors."""
        errors = {"name": ["Required"], "age": ["Must be positive"]}
        exc = ValidationError("Validation failed", errors=errors)
        assert exc.errors == errors
    
    def test_validation_error_to_dict(self):
        """Test ValidationError to_dict method."""
        errors = {"name": ["Required"]}
        exc = ValidationError("Validation failed", errors=errors)
        result = exc.to_dict()
        
        assert result["error"] == "Validation failed"
        assert result["errors"] == errors
    
    def test_validation_error_to_dict_no_errors(self):
        """Test ValidationError to_dict without errors."""
        exc = ValidationError("Validation failed")
        result = exc.to_dict()
        
        assert result["error"] == "Validation failed"
        assert "errors" not in result


class TestNotFoundError:
    """Tests for NotFoundError."""
    
    def test_not_found_error_creation(self):
        """Test creating NotFoundError."""
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.detail == "Not Found"
    
    def test_not_found_error_custom_message(self):
        """Test NotFoundError with custom message."""
        exc = NotFoundError("User not found")
        assert exc.status_code == 404
        assert exc.detail == "User not found"


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""
    
    def test_unauthorized_error_creation(self):
        """Test creating UnauthorizedError."""
        exc = UnauthorizedError()
        assert exc.status_code == 401
        assert exc.detail == "Unauthorized"
    
    def test_unauthorized_error_custom_message(self):
        """Test UnauthorizedError with custom message."""
        exc = UnauthorizedError("Invalid token")
        assert exc.status_code == 401
        assert exc.detail == "Invalid token"


class TestForbiddenError:
    """Tests for ForbiddenError."""
    
    def test_forbidden_error_creation(self):
        """Test creating ForbiddenError."""
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.detail == "Forbidden"
    
    def test_forbidden_error_custom_message(self):
        """Test ForbiddenError with custom message."""
        exc = ForbiddenError("Access denied")
        assert exc.status_code == 403
        assert exc.detail == "Access denied"


class TestInternalServerError:
    """Tests for InternalServerError."""
    
    def test_internal_server_error_creation(self):
        """Test creating InternalServerError."""
        exc = InternalServerError()
        assert exc.status_code == 500
        assert exc.detail == "Internal Server Error"
    
    def test_internal_server_error_custom_message(self):
        """Test InternalServerError with custom message."""
        exc = InternalServerError("Database error")
        assert exc.status_code == 500
        assert exc.detail == "Database error"


class TestPayloadTooLargeError:
    """Tests for PayloadTooLargeError."""
    
    def test_payload_too_large_error_creation(self):
        """Test creating PayloadTooLargeError."""
        exc = PayloadTooLargeError()
        assert exc.status_code == 413
        assert exc.detail == "Payload Too Large"
    
    def test_payload_too_large_error_custom_message(self):
        """Test PayloadTooLargeError with custom message."""
        exc = PayloadTooLargeError("Request body exceeds 10MB")
        assert exc.status_code == 413
        assert exc.detail == "Request body exceeds 10MB"

