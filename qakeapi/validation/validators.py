"""
Data validators for the framework.

This module provides various validators for different data types.
All validators use only Python standard library.
"""

import re
import email.utils
from typing import Any, Optional, List, Dict, Callable
from datetime import datetime
from urllib.parse import urlparse


class ValidationError(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
        """
        self.message = message
        self.field = field
        super().__init__(self.message)


class BaseValidator:
    """Base class for all validators."""
    
    def validate(self, value: Any) -> Any:
        """
        Validate a value.
        
        Args:
            value: Value to validate
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If validation fails
        """
        raise NotImplementedError


class StringValidator(BaseValidator):
    """Validator for string values."""
    
    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        strip: bool = True,
    ):
        """
        Initialize string validator.
        
        Args:
            min_length: Minimum string length
            max_length: Maximum string length
            pattern: Regex pattern to match
            strip: Whether to strip whitespace
        """
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.strip = strip
    
    def validate(self, value: Any) -> str:
        """Validate string value."""
        if not isinstance(value, str):
            value = str(value)
        
        if self.strip:
            value = value.strip()
        
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"String must be at least {self.min_length} characters long"
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"String must be at most {self.max_length} characters long"
            )
        
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(f"String does not match pattern: {self.pattern.pattern}")
        
        return value


class IntegerValidator(BaseValidator):
    """Validator for integer values."""
    
    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        """
        Initialize integer validator.
        
        Args:
            min_value: Minimum value
            max_value: Maximum value
        """
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> int:
        """Validate integer value."""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Cannot convert {value} to integer")
        
        if self.min_value is not None and int_value < self.min_value:
            raise ValidationError(
                f"Integer must be at least {self.min_value}"
            )
        
        if self.max_value is not None and int_value > self.max_value:
            raise ValidationError(
                f"Integer must be at most {self.max_value}"
            )
        
        return int_value


class FloatValidator(BaseValidator):
    """Validator for float values."""
    
    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        """
        Initialize float validator.
        
        Args:
            min_value: Minimum value
            max_value: Maximum value
        """
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> float:
        """Validate float value."""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Cannot convert {value} to float")
        
        if self.min_value is not None and float_value < self.min_value:
            raise ValidationError(
                f"Float must be at least {self.min_value}"
            )
        
        if self.max_value is not None and float_value > self.max_value:
            raise ValidationError(
                f"Float must be at most {self.max_value}"
            )
        
        return float_value


class BooleanValidator(BaseValidator):
    """Validator for boolean values."""
    
    def validate(self, value: Any) -> bool:
        """Validate boolean value."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ("true", "1", "yes", "on"):
                return True
            if value_lower in ("false", "0", "no", "off", ""):
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValidationError(f"Cannot convert {value} to boolean")


class EmailValidator(BaseValidator):
    """Validator for email addresses."""
    
    def __init__(self, check_deliverable: bool = False):
        """
        Initialize email validator.
        
        Args:
            check_deliverable: Whether to check if email is deliverable
                (not implemented, always False)
        """
        self.check_deliverable = check_deliverable
        # RFC 5322 compliant email regex (simplified)
        self.pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def validate(self, value: Any) -> str:
        """Validate email address."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        # Use email.utils for basic validation
        try:
            email.utils.parseaddr(value)
        except Exception:
            raise ValidationError(f"Invalid email format: {value}")
        
        # Additional regex check
        if not self.pattern.match(value):
            raise ValidationError(f"Invalid email format: {value}")
        
        return value


class URLValidator(BaseValidator):
    """Validator for URL addresses."""
    
    def __init__(
        self,
        schemes: Optional[List[str]] = None,
        require_absolute: bool = True,
    ):
        """
        Initialize URL validator.
        
        Args:
            schemes: Allowed URL schemes (default: http, https)
            require_absolute: Whether to require absolute URLs
        """
        self.schemes = schemes or ["http", "https"]
        self.require_absolute = require_absolute
    
    def validate(self, value: Any) -> str:
        """Validate URL."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        if not value:
            raise ValidationError("URL cannot be empty")
        
        try:
            parsed = urlparse(value)
        except Exception:
            raise ValidationError(f"Invalid URL format: {value}")
        
        if self.require_absolute and not parsed.scheme:
            raise ValidationError("URL must be absolute (include scheme)")
        
        if parsed.scheme and parsed.scheme not in self.schemes:
            raise ValidationError(
                f"URL scheme must be one of: {', '.join(self.schemes)}"
            )
        
        if not parsed.netloc and self.require_absolute:
            raise ValidationError("URL must have a valid domain")
        
        return value


class DateTimeValidator(BaseValidator):
    """Validator for datetime values."""
    
    def __init__(
        self,
        formats: Optional[List[str]] = None,
        min_value: Optional[datetime] = None,
        max_value: Optional[datetime] = None,
    ):
        """
        Initialize datetime validator.
        
        Args:
            formats: List of datetime format strings
            min_value: Minimum datetime value
            max_value: Maximum datetime value
        """
        self.formats = formats or [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S.%f",
        ]
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> datetime:
        """Validate datetime value."""
        if isinstance(value, datetime):
            dt_value = value
        elif isinstance(value, str):
            dt_value = None
            for fmt in self.formats:
                try:
                    dt_value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            
            if dt_value is None:
                raise ValidationError(
                    f"Cannot parse datetime: {value}. "
                    f"Expected formats: {', '.join(self.formats)}"
                )
        else:
            raise ValidationError(f"Cannot convert {value} to datetime")
        
        if self.min_value and dt_value < self.min_value:
            raise ValidationError(
                f"Datetime must be after {self.min_value}"
            )
        
        if self.max_value and dt_value > self.max_value:
            raise ValidationError(
                f"Datetime must be before {self.max_value}"
            )
        
        return dt_value


class ListValidator(BaseValidator):
    """Validator for list values."""
    
    def __init__(
        self,
        item_validator: Optional[BaseValidator] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ):
        """
        Initialize list validator.
        
        Args:
            item_validator: Validator for list items
            min_length: Minimum list length
            max_length: Maximum list length
        """
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any) -> List[Any]:
        """Validate list value."""
        if not isinstance(value, list):
            # Try to convert to list
            if isinstance(value, (str, tuple)):
                value = list(value)
            else:
                raise ValidationError(f"Cannot convert {value} to list")
        
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"List must have at least {self.min_length} items"
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"List must have at most {self.max_length} items"
            )
        
        if self.item_validator:
            validated_list = []
            for item in value:
                validated_list.append(self.item_validator.validate(item))
            return validated_list
        
        return value


class DictValidator(BaseValidator):
    """Validator for dictionary values."""
    
    def __init__(
        self,
        schema: Optional[Dict[str, BaseValidator]] = None,
        required_keys: Optional[List[str]] = None,
    ):
        """
        Initialize dict validator.
        
        Args:
            schema: Dictionary of field validators
            required_keys: List of required keys
        """
        self.schema = schema or {}
        self.required_keys = required_keys or []
    
    def validate(self, value: Any) -> Dict[str, Any]:
        """Validate dictionary value."""
        if not isinstance(value, dict):
            raise ValidationError(f"Cannot convert {value} to dictionary")
        
        # Check required keys
        for key in self.required_keys:
            if key not in value:
                raise ValidationError(f"Required key missing: {key}")
        
        validated_dict = {}
        
        # Validate known fields
        for key, validator in self.schema.items():
            if key in value:
                try:
                    validated_dict[key] = validator.validate(value[key])
                except ValidationError as e:
                    e.field = key
                    raise
            elif key in self.required_keys:
                raise ValidationError(f"Required key missing: {key}")
        
        # Keep unknown fields
        for key, val in value.items():
            if key not in validated_dict:
                validated_dict[key] = val
        
        return validated_dict

