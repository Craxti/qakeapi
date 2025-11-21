"""
Data models for the framework.

This module provides a simple model system for data validation and serialization.
"""

from typing import Any, Dict, Optional, Type, get_args, get_origin, get_type_hints

from .validators import (
    BaseValidator,
    BooleanValidator,
    DateTimeValidator,
    EmailValidator,
    FloatValidator,
    IntegerValidator,
    StringValidator,
    URLValidator,
    ValidationError,
)


class Field:
    """Represents a model field with validation."""

    def __init__(
        self,
        validator: Optional[BaseValidator] = None,
        default: Any = None,
        required: bool = True,
    ):
        """
        Initialize field.

        Args:
            validator: Validator instance
            default: Default value
            required: Whether field is required
        """
        self.validator = validator
        self.default = default
        self.required = required


class BaseModel:
    """
    Base class for data models.

    Provides validation and serialization for model instances.
    """

    def __init__(self, **kwargs):
        """
        Initialize model instance.

        Args:
            **kwargs: Field values
        """
        # Get field definitions from class
        fields = self._get_fields()

        # Check for extra fields - by default, forbid extra fields for request models
        # Response models can allow extra fields
        extra_fields = set(kwargs.keys()) - set(fields.keys())
        if extra_fields:
            # Check if model has model_config with extra setting
            if hasattr(self, 'model_config'):
                extra_setting = getattr(self.model_config, 'extra', 'forbid')
                if extra_setting == 'forbid':
                    raise ValidationError(f"Extra fields not allowed: {', '.join(extra_fields)}")
            else:
                # Default: forbid extra fields (for request models)
                # But allow for response models (they can have extra fields)
                # We'll check class name or a flag
                class_name = self.__class__.__name__
                if 'Request' in class_name or 'Input' in class_name:
                    raise ValidationError(f"Extra fields not allowed: {', '.join(extra_fields)}")

        # Set field values
        for field_name, field_def in fields.items():
            if field_name in kwargs:
                value = kwargs[field_name]
            elif field_def.default is not None:
                value = field_def.default
            elif field_def.required:
                raise ValidationError(f"Required field missing: {field_name}")
            else:
                value = None

            # Validate and set value
            if value is not None and field_def.validator:
                try:
                    value = field_def.validator.validate(value)
                except ValidationError as e:
                    e.field = field_name
                    raise

            setattr(self, field_name, value)

    @classmethod
    def _get_fields(cls) -> Dict[str, Field]:
        """
        Get field definitions from class.

        Returns:
            Dictionary of field definitions
        """
        fields = {}

        # Check for explicit field definitions
        for name in dir(cls):
            if not name.startswith("_") and isinstance(getattr(cls, name), Field):
                fields[name] = getattr(cls, name)

        # If no explicit fields, infer from type hints
        if not fields:
            type_hints = get_type_hints(cls)
            for name, type_hint in type_hints.items():
                if name.startswith("_"):
                    continue

                # Create validator from type hint
                validator = cls._create_validator_from_type(type_hint)
                fields[name] = Field(validator=validator, required=True)

        return fields

    @classmethod
    def _create_validator_from_type(cls, type_hint: Type) -> Optional[BaseValidator]:
        """
        Create validator from type hint.

        Args:
            type_hint: Type hint

        Returns:
            Validator instance or None
        """
        # Handle Optional types
        origin = get_origin(type_hint)
        if origin is not None:
            args = get_args(type_hint)
            if len(args) > 0:
                type_hint = args[0]

        # Map types to validators
        if type_hint == str:
            return StringValidator()
        elif type_hint == int:
            return IntegerValidator()
        elif type_hint == float:
            return FloatValidator()
        elif type_hint == bool:
            return BooleanValidator()

        return None

    def dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Returns:
            Dictionary representation of model
        """
        result = {}
        fields = self._get_fields()

        for field_name in fields.keys():
            value = getattr(self, field_name, None)
            if value is not None:
                if isinstance(value, BaseModel):
                    result[field_name] = value.dict()
                elif isinstance(value, list):
                    result[field_name] = [
                        item.dict() if isinstance(item, BaseModel) else item
                        for item in value
                    ]
                else:
                    result[field_name] = value

        return result

    def json(self) -> str:
        """
        Convert model to JSON string.

        Returns:
            JSON string representation
        """
        import json

        return json.dumps(self.dict(), default=str)

    @classmethod
    def parse_obj(cls, obj: Dict[str, Any]) -> "BaseModel":
        """
        Parse object from dictionary.

        Args:
            obj: Dictionary to parse

        Returns:
            Model instance
        """
        return cls(**obj)

    @classmethod
    def parse_json(cls, json_str: str) -> "BaseModel":
        """
        Parse object from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Model instance
        """
        import json

        return cls.parse_obj(json.loads(json_str))
