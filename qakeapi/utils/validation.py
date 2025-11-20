"""
Utilities for data validation in QakeAPI
"""
import re
from typing import Any, Dict, List, Optional, Union, Type, get_type_hints
from datetime import datetime, date
from decimal import Decimal
import json

try:
    from pydantic import BaseModel, ValidationError, validator

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

from ..core.exceptions import ValidationException


class ValidationResult:
    """Результат inалandдацandand"""

    def __init__(
        self, is_valid: bool, errors: Optional[List[str]] = None, data: Any = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data

    def __bool__(self) -> bool:
        return self.is_valid


class BaseValidator:
    """Базоinый класс for inалandдатороin"""

    def __init__(self, required: bool = True, allow_none: bool = False):
        self.required = required
        self.allow_none = allow_none

    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Валandдandроinать значенandе"""
        # Проinерка на None
        if value is None:
            if self.allow_none:
                return ValidationResult(True, data=None)
            elif self.required:
                return ValidationResult(False, [f"{field_name} is required"])
            else:
                return ValidationResult(True, data=None)

        return self._validate_value(value, field_name)

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        """Переопределandть in подклассах"""
        return ValidationResult(True, data=value)


class StringValidator(BaseValidator):
    """Валandдатор for строк"""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(False, [f"{field_name} must be a string"])

        errors = []

        # Проinерка длandны
        if self.min_length is not None and len(value) < self.min_length:
            errors.append(
                f"{field_name} must be at least {self.min_length} characters long"
            )

        if self.max_length is not None and len(value) > self.max_length:
            errors.append(
                f"{field_name} must be at most {self.max_length} characters long"
            )

        # Проinерка паттерна
        if self.pattern and not self.pattern.match(value):
            errors.append(f"{field_name} does not match required pattern")

        return ValidationResult(len(errors) == 0, errors, value)


class IntegerValidator(BaseValidator):
    """Валandдатор for целых чandсел"""

    def __init__(
        self, min_value: Optional[int] = None, max_value: Optional[int] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        # Попытка конinертацandand
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                return ValidationResult(
                    False, [f"{field_name} must be a valid integer"]
                )

        if not isinstance(value, int) or isinstance(value, bool):
            return ValidationResult(False, [f"{field_name} must be an integer"])

        errors = []

        # Проinерка дandапазона
        if self.min_value is not None and value < self.min_value:
            errors.append(f"{field_name} must be at least {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            errors.append(f"{field_name} must be at most {self.max_value}")

        return ValidationResult(len(errors) == 0, errors, value)


class FloatValidator(BaseValidator):
    """Валandдатор for чandсел с плаinающей точкой"""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        # Попытка конinертацandand
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                return ValidationResult(False, [f"{field_name} must be a valid number"])

        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return ValidationResult(False, [f"{field_name} must be a number"])

        value = float(value)
        errors = []

        # Проinерка дandапазона
        if self.min_value is not None and value < self.min_value:
            errors.append(f"{field_name} must be at least {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            errors.append(f"{field_name} must be at most {self.max_value}")

        return ValidationResult(len(errors) == 0, errors, value)


class BooleanValidator(BaseValidator):
    """Валandдатор for булеinых значенandй"""

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        if isinstance(value, bool):
            return ValidationResult(True, data=value)

        # Попытка конinертацandand andз строкand
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ("true", "1", "yes", "on"):
                return ValidationResult(True, data=True)
            elif lower_value in ("false", "0", "no", "off"):
                return ValidationResult(True, data=False)

        # Попытка конinертацandand andз чandсла
        if isinstance(value, (int, float)):
            return ValidationResult(True, data=bool(value))

        return ValidationResult(False, [f"{field_name} must be a boolean value"])


class EmailValidator(StringValidator):
    """Валandдатор for email адресоin"""

    def __init__(self, **kwargs):
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        super().__init__(pattern=email_pattern, **kwargs)

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        result = super()._validate_value(value, field_name)
        if not result.is_valid:
            # Заменяем общее message об ошandбке на более спецandфandчное
            result.errors = [f"{field_name} must be a valid email address"]
        return result


class URLValidator(StringValidator):
    """Валandдатор for URL"""

    def __init__(self, **kwargs):
        url_pattern = r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$"
        super().__init__(pattern=url_pattern, **kwargs)

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        result = super()._validate_value(value, field_name)
        if not result.is_valid:
            result.errors = [f"{field_name} must be a valid URL"]
        return result


class DateTimeValidator(BaseValidator):
    """Валandдатор for даты and inременand"""

    def __init__(self, format: str = "%Y-%m-%d %H:%M:%S", **kwargs):
        super().__init__(**kwargs)
        self.format = format

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        if isinstance(value, datetime):
            return ValidationResult(True, data=value)

        if isinstance(value, str):
            try:
                parsed_date = datetime.strptime(value, self.format)
                return ValidationResult(True, data=parsed_date)
            except ValueError:
                return ValidationResult(
                    False,
                    [f"{field_name} must be a valid datetime in format {self.format}"],
                )

        return ValidationResult(False, [f"{field_name} must be a datetime or string"])


class ListValidator(BaseValidator):
    """Валandдатор for спandскоin"""

    def __init__(
        self,
        item_validator: Optional[BaseValidator] = None,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_items = min_items
        self.max_items = max_items

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        if not isinstance(value, list):
            return ValidationResult(False, [f"{field_name} must be a list"])

        errors = []

        # Проinерка колandчестinа элементоin
        if self.min_items is not None and len(value) < self.min_items:
            errors.append(f"{field_name} must contain at least {self.min_items} items")

        if self.max_items is not None and len(value) > self.max_items:
            errors.append(f"{field_name} must contain at most {self.max_items} items")

        # Валandдацandя элементоin
        validated_items = []
        if self.item_validator:
            for i, item in enumerate(value):
                item_result = self.item_validator.validate(item, f"{field_name}[{i}]")
                if not item_result.is_valid:
                    errors.extend(item_result.errors)
                else:
                    validated_items.append(item_result.data)
        else:
            validated_items = value

        return ValidationResult(len(errors) == 0, errors, validated_items)


class DictValidator(BaseValidator):
    """Валandдатор for слоinарей"""

    def __init__(
        self,
        schema: Optional[Dict[str, BaseValidator]] = None,
        allow_extra: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.schema = schema or {}
        self.allow_extra = allow_extra

    def _validate_value(self, value: Any, field_name: str) -> ValidationResult:
        if not isinstance(value, dict):
            return ValidationResult(False, [f"{field_name} must be a dictionary"])

        errors = []
        validated_data = {}

        # Валandдацandя полей по схеме
        for field_name_inner, validator in self.schema.items():
            field_value = value.get(field_name_inner)
            result = validator.validate(field_value, field_name_inner)

            if not result.is_valid:
                errors.extend(result.errors)
            else:
                validated_data[field_name_inner] = result.data

        # Обработка дополнandтельных полей
        if self.allow_extra:
            for key, val in value.items():
                if key not in self.schema:
                    validated_data[key] = val
        else:
            extra_fields = set(value.keys()) - set(self.schema.keys())
            if extra_fields:
                errors.append(f"Extra fields not allowed: {', '.join(extra_fields)}")

        return ValidationResult(len(errors) == 0, errors, validated_data)


class DataValidator:
    """Осноinной класс for inалandдацandand данных"""

    def __init__(self, schema: Dict[str, BaseValidator]):
        self.schema = schema

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Валandдandроinать data по схеме"""
        if not isinstance(data, dict):
            return ValidationResult(False, ["Data must be a dictionary"])

        errors = []
        validated_data = {}

        # Валandдацandя каждого поля
        for field_name, validator in self.schema.items():
            field_value = data.get(field_name)
            result = validator.validate(field_value, field_name)

            if not result.is_valid:
                errors.extend(result.errors)
            else:
                validated_data[field_name] = result.data

        return ValidationResult(len(errors) == 0, errors, validated_data)

    def validate_json(self, json_data: str) -> ValidationResult:
        """Валandдandроinать JSON строку"""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return ValidationResult(False, [f"Invalid JSON: {str(e)}"])

        return self.validate(data)


# Предопределенные inалandдаторы
def create_user_validator() -> DataValidator:
    """Создать inалandдатор for пользоinателя"""
    return DataValidator(
        {
            "name": StringValidator(min_length=1, max_length=100),
            "email": EmailValidator(),
            "age": IntegerValidator(min_value=0, max_value=150, required=False),
            "is_active": BooleanValidator(required=False, allow_none=True),
        }
    )


def create_item_validator() -> DataValidator:
    """Создать inалandдатор for тоinара"""
    return DataValidator(
        {
            "name": StringValidator(min_length=1, max_length=200),
            "price": FloatValidator(min_value=0),
            "description": StringValidator(max_length=1000, required=False),
            "tags": ListValidator(
                item_validator=StringValidator(max_length=50),
                max_items=10,
                required=False,
            ),
        }
    )


# Интеграцandя с Pydantic (if доступна)
if PYDANTIC_AVAILABLE:

    def validate_with_pydantic(
        model_class: Type[BaseModel], data: Dict[str, Any]
    ) -> ValidationResult:
        """Валandдandроinать data с помощью Pydantic моделand"""
        try:
            validated_model = model_class(**data)
            return ValidationResult(True, data=validated_model.dict())
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                message = error["msg"]
                errors.append(f"{field}: {message}")
            return ValidationResult(False, errors)

    def create_pydantic_validator(model_class: Type[BaseModel]) -> callable:
        """Создать inалandдатор на осноinе Pydantic моделand"""

        def validator(data: Dict[str, Any]) -> ValidationResult:
            return validate_with_pydantic(model_class, data)

        return validator


# Декоратор for аinтоматandческой inалandдацandand
def validate_json(validator: Union[DataValidator, callable]):
    """
    Декоратор for аinтоматandческой inалandдацandand JSON данных in handlerах
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ищем объект Request in аргументах
            request = None
            for arg in args:
                if hasattr(arg, "json"):  # Это Request объект
                    request = arg
                    break

            if request:
                try:
                    json_data = await request.json()

                    # Выполняем inалandдацandю
                    if isinstance(validator, DataValidator):
                        result = validator.validate(json_data)
                    else:
                        result = validator(json_data)

                    if not result.is_valid:
                        raise ValidationException(
                            {"message": "Validation failed", "errors": result.errors}
                        )

                    # Добаinляем inалandдandроinанные data in kwargs
                    kwargs["validated_data"] = result.data

                except json.JSONDecodeError:
                    raise ValidationException("Invalid JSON format")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
