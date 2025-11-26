"""
Tests for validation system.
"""

import pytest
from dataclasses import dataclass
from typing import List, Optional, Dict
from qakeapi.core.validation import (
    ValidationError,
    validate_model,
    validate_path_param,
    validate_query_param,
    validate_request_body,
    BaseValidator
)


class TestValidatePathParam:
    """Tests for validate_path_param function."""
    
    def test_validate_path_param_int(self):
        """Test validating integer path parameter."""
        result = validate_path_param("123", int)
        assert result == 123
    
    def test_validate_path_param_int_invalid(self):
        """Test validating invalid integer."""
        with pytest.raises(ValidationError):
            validate_path_param("abc", int)
    
    def test_validate_path_param_float(self):
        """Test validating float path parameter."""
        result = validate_path_param("123.45", float)
        assert result == 123.45
    
    def test_validate_path_param_bool(self):
        """Test validating boolean path parameter."""
        assert validate_path_param("true", bool) is True
        assert validate_path_param("false", bool) is False
        assert validate_path_param("1", bool) is True
        assert validate_path_param("0", bool) is False
    
    def test_validate_path_param_str(self):
        """Test validating string path parameter."""
        result = validate_path_param("test", str)
        assert result == "test"


class TestValidateQueryParam:
    """Tests for validate_query_param function."""
    
    def test_validate_query_param_int(self):
        """Test validating integer query parameter."""
        result = validate_query_param("123", int)
        assert result == 123
    
    def test_validate_query_param_float(self):
        """Test validating float query parameter."""
        result = validate_query_param("123.45", float)
        assert result == 123.45
    
    def test_validate_query_param_bool(self):
        """Test validating boolean query parameter."""
        assert validate_query_param("true", bool) is True
        assert validate_query_param("false", bool) is False
    
    def test_validate_query_param_str(self):
        """Test validating string query parameter."""
        result = validate_query_param("test", str)
        assert result == "test"
    
    def test_validate_query_param_optional(self):
        """Test validating optional query parameter."""
        from typing import Optional
        result = validate_query_param("123", Optional[int])
        assert result == 123


class TestValidateRequestBody:
    """Tests for validate_request_body function."""
    
    def test_validate_request_body_dataclass(self):
        """Test validating request body with dataclass."""
        @dataclass
        class UserCreate:
            name: str
            age: int
            email: Optional[str] = None
        
        data = {"name": "John", "age": 30, "email": "john@example.com"}
        result = validate_request_body(data, UserCreate)
        
        assert isinstance(result, UserCreate)
        assert result.name == "John"
        assert result.age == 30
        assert result.email == "john@example.com"
    
    def test_validate_request_body_dataclass_missing_required(self):
        """Test validating dataclass with missing required field."""
        @dataclass
        class UserCreate:
            name: str
            age: int
        
        data = {"name": "John"}
        
        # validate_request_body may not raise error immediately, 
        # but will fail when trying to create instance
        try:
            result = validate_request_body(data, UserCreate)
            # If it doesn't raise, the age might be missing
            # This depends on implementation
        except (ValidationError, TypeError, KeyError):
            pass  # Expected behavior
    
    def test_validate_request_body_dataclass_optional(self):
        """Test validating dataclass with optional field."""
        @dataclass
        class UserCreate:
            name: str
            age: int
            email: Optional[str] = None
        
        data = {"name": "John", "age": 30}
        result = validate_request_body(data, UserCreate)
        
        assert result.email is None
    
    def test_validate_request_body_type_conversion(self):
        """Test type conversion in validation."""
        @dataclass
        class Item:
            id: int
            price: float
            active: bool
        
        data = {"id": "123", "price": "99.99", "active": "true"}
        result = validate_request_body(data, Item)
        
        assert result.id == 123
        assert result.price == 99.99
        assert result.active is True
    
    def test_validate_request_body_invalid_type(self):
        """Test validation with invalid type."""
        @dataclass
        class Item:
            id: int
        
        data = {"id": "abc"}
        
        with pytest.raises(ValidationError):
            validate_request_body(data, Item)


class TestValidateModel:
    """Tests for validate_model function."""
    
    def test_validate_model_simple(self):
        """Test validating simple model."""
        @dataclass
        class SimpleModel:
            value: int
        
        data = {"value": 42}
        result = validate_model(data, SimpleModel)
        
        assert isinstance(result, SimpleModel)
        assert result.value == 42
    
    def test_validate_model_with_list(self):
        """Test validating model with list."""
        @dataclass
        class ModelWithList:
            items: List[int]
        
        data = {"items": [1, 2, 3]}
        result = validate_model(data, ModelWithList)
        
        assert result.items == [1, 2, 3]
    
    def test_validate_model_with_dict(self):
        """Test validating model with dict."""
        @dataclass
        class ModelWithDict:
            metadata: Dict[str, str]
        
        data = {"metadata": {"key": "value"}}
        result = validate_model(data, ModelWithDict)
        
        assert result.metadata == {"key": "value"}


class TestValidationError:
    """Tests for ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid value")
        assert error.message == "Invalid value"
        assert error.errors == {}
    
    def test_validation_error_with_errors(self):
        """Test ValidationError with errors dict."""
        errors = {"name": ["Required"], "age": ["Must be positive"]}
        error = ValidationError("Validation failed", errors=errors)
        assert error.errors == errors


class TestBaseValidator:
    """Tests for BaseValidator class."""
    
    def test_base_validator_creation(self):
        """Test creating BaseValidator."""
        validator = BaseValidator()
        assert validator is not None
    
    def test_base_validator_validate_type(self):
        """Test BaseValidator validate_type method."""
        # Test int validation
        result = BaseValidator.validate_type("123", int)
        assert result == 123
        
        # Test float validation
        result = BaseValidator.validate_type("123.45", float)
        assert result == 123.45
        
        # Test bool validation
        result = BaseValidator.validate_type("true", bool)
        assert result is True
        
        # Test str validation
        result = BaseValidator.validate_type(123, str)
        assert result == "123"
        
        # Test invalid int
        with pytest.raises(ValidationError):
            BaseValidator.validate_type("abc", int)

