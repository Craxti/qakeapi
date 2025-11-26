"""
Validation system for QakeAPI.

Provides validation functionality similar to Pydantic, but using only
standard library for zero dependencies.
"""

import inspect
from typing import Any, Dict, List, Optional, Type, TypeVar, get_origin, get_args
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime

T = TypeVar("T")


class ValidationError(Exception):
    """Raised when validation fails (internal validation error)."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, List[str]]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            errors: Dictionary of field errors {field: [errors]}
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


class BaseValidator:
    """Base validator class."""
    
    @staticmethod
    def validate_type(value: Any, expected_type: Type) -> Any:
        """
        Validate and convert value to expected type.
        
        Args:
            value: Value to validate
            expected_type: Expected type
            
        Returns:
            Converted value
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            return None
        
        # Handle Optional types
        origin = get_origin(expected_type)
        if origin is type(None) or (origin is not None and type(None) in get_args(expected_type)):
            # It's Optional, get the actual type
            args = get_args(expected_type)
            if args:
                actual_type = args[0] if args[0] is not type(None) else args[1]
                return BaseValidator.validate_type(value, actual_type)
            return value
        
        # Handle List types
        if origin is list:
            if not isinstance(value, list):
                raise ValidationError(f"Expected list, got {type(value).__name__}")
            args = get_args(expected_type)
            item_type = args[0] if args else Any
            return [BaseValidator.validate_type(item, item_type) for item in value]
        
        # Handle Dict types
        if origin is dict:
            if not isinstance(value, dict):
                raise ValidationError(f"Expected dict, got {type(value).__name__}")
            return value  # Dict validation can be enhanced
        
        # Handle basic types
        if expected_type == int:
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid integer: {value}")
        
        if expected_type == float:
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid float: {value}")
        
        if expected_type == bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        
        if expected_type == str:
            return str(value)
        
        # For custom classes, try to instantiate
        if inspect.isclass(expected_type):
            return value
        
        return value


def validate_model(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Validate data against a model class.
    
    Args:
        data: Dictionary of data to validate
        model_class: Model class (dataclass or class with __annotations__)
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If validation fails
        
    Example:
        ```python
        @dataclass
        class User:
            name: str
            age: int
            email: Optional[str] = None
        
        data = {"name": "John", "age": 30}
        user = validate_model(data, User)
        ```
    """
    errors: Dict[str, List[str]] = {}
    validated_data: Dict[str, Any] = {}
    
    # Get field annotations
    if is_dataclass(model_class):
        model_fields = {f.name: f for f in fields(model_class)}
        annotations = model_class.__annotations__
    elif hasattr(model_class, "__annotations__"):
        annotations = model_class.__annotations__
        model_fields = {}
    else:
        raise ValidationError(f"Model class {model_class} must have type annotations")
    
    # Validate each field
    for field_name, field_type in annotations.items():
        value = data.get(field_name)
        
        # Check if field is required
        if is_dataclass(model_class) and field_name in model_fields:
            field = model_fields[field_name]
            is_required = field.default == inspect.Parameter.empty and field.default_factory == inspect.Parameter.empty
        else:
            is_required = True
        
        # Validate required fields
        if value is None and is_required:
            errors.setdefault(field_name, []).append("Field is required")
            continue
        
        # Skip None values for optional fields
        if value is None:
            validated_data[field_name] = None
            continue
        
        # Validate type
        try:
            validated_data[field_name] = BaseValidator.validate_type(value, field_type)
        except ValidationError as e:
            errors.setdefault(field_name, []).append(str(e))
    
    # Check for extra fields (optional - can be disabled)
    # Allow extra fields by default, but can be configured to reject them
    extra_fields = set(data.keys()) - set(annotations.keys())
    # Extra fields are allowed by default
    
    # Raise error if validation failed
    if errors:
        raise ValidationError("Validation failed", errors)
    
    # Create instance
    try:
        if is_dataclass(model_class):
            return model_class(**validated_data)
        else:
            # For regular classes, try to instantiate
            instance = model_class()
            for key, value in validated_data.items():
                setattr(instance, key, value)
            return instance
    except Exception as e:
        raise ValidationError(f"Failed to create instance: {str(e)}")


def validate_request_body(data: Any, expected_type: Type[T]) -> T:
    """
    Validate request body data.
    
    Args:
        data: Request body data (dict or None)
        expected_type: Expected type
        
    Returns:
        Validated instance
        
    Raises:
        ValidationError: If validation fails
    """
    if data is None:
        raise ValidationError("Request body is required")
    
    if not isinstance(data, dict):
        raise ValidationError(f"Expected dict, got {type(data).__name__}")
    
    return validate_model(data, expected_type)


def validate_query_param(value: Any, param_type: Type) -> Any:
    """
    Validate query parameter.
    
    Args:
        value: Parameter value
        param_type: Expected type
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return None
    
    return BaseValidator.validate_type(value, param_type)


def validate_path_param(value: str, param_type: Type) -> Any:
    """
    Validate path parameter.
    
    Args:
        value: Parameter value (string from URL)
        param_type: Expected type
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    return BaseValidator.validate_type(value, param_type)

