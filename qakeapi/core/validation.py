from typing import Any, Dict, Optional, Type, TypeVar

try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    BaseModel = None  # type: ignore
    ValidationError = None  # type: ignore

from .responses import Response

T = TypeVar("T")


class DataValidator:
    """Base validator class"""

    def validate(self, data: Any) -> Any:
        """Validate data"""
        if data is None:
            raise ValueError("Data cannot be None")
        return data


class PydanticValidator:
    """Pydantic model validator"""

    def __init__(self, model_class: Type[Any]):
        if BaseModel is None:
            raise ImportError(
                "pydantic is required for PydanticValidator. "
                "Install it with: pip install pydantic"
            )
        if not issubclass(model_class, BaseModel):
            raise TypeError("model_class must be a Pydantic model")
        self.model_class = model_class

    def validate(self, data: Dict[str, Any]) -> BaseModel:
        """Validate data against Pydantic model"""
        try:
            # Создаем модель с exclude_unset=True, чтобы использовать значения по умолчанию
            model = self.model_class(**data, exclude_unset=True)
            # Преобразуем в словарь и обратно для применения значений по умолчанию
            return self.model_class(**model.model_dump())
        except ValidationError as e:
            raise ValueError(f"Validation error: {str(e)}")


class ValidationFactory:
    """Factory for creating validators"""

    VALIDATORS = {"data": DataValidator, "pydantic": PydanticValidator}

    @classmethod
    def create(
        cls, validator_type: str, model_class: Optional[Type[Any]] = None
    ) -> Any:
        """Create validator instance"""
        if validator_type not in cls.VALIDATORS:
            raise ValueError(f"Unknown validator type: {validator_type}")

        validator_class = cls.VALIDATORS[validator_type]

        if validator_type == "pydantic":
            if BaseModel is None:
                raise ImportError(
                    "pydantic is required for pydantic validator. "
                    "Install it with: pip install pydantic"
                )
            if not model_class:
                raise ValueError("model_class is required for pydantic validator")
            return validator_class(model_class)

        return validator_class()


class RequestValidator:
    """Валидатор запросов с использованием Pydantic"""

    @staticmethod
    async def validate_request_body(
        request_body: Dict[str, Any], model: Type[T]
    ) -> Optional[T]:
        """Валидация тела запроса"""
        if BaseModel is None or ValidationError is None:
            raise ImportError(
                "pydantic is required for validate_request_body. "
                "Install it with: pip install pydantic"
            )
        try:
            # Используем exclude_unset=True для применения значений по умолчанию
            validated = model(**request_body, exclude_unset=True)
            # Преобразуем в словарь и обратно для применения значений по умолчанию
            return model(**validated.model_dump())
        except ValidationError as e:
            return None

    @staticmethod
    def validate_path_params(
        path_params: Dict[str, str], model: Type[T]
    ) -> Optional[T]:
        """Валидация параметров пути"""
        if BaseModel is None or ValidationError is None:
            raise ImportError(
                "pydantic is required for validate_path_params. "
                "Install it with: pip install pydantic"
            )
        try:
            # Используем exclude_unset=True для применения значений по умолчанию
            validated = model(**path_params, exclude_unset=True)
            # Преобразуем в словарь и обратно для применения значений по умолчанию
            return model(**validated.model_dump())
        except ValidationError:
            return None

    @staticmethod
    def validate_query_params(
        query_params: Dict[str, Any], model: Type[T]
    ) -> Optional[T]:
        """Валидация параметров запроса"""
        if BaseModel is None or ValidationError is None:
            raise ImportError(
                "pydantic is required for validate_query_params. "
                "Install it with: pip install pydantic"
            )
        try:
            # Преобразуем списки с одним элементом в скалярные значения
            cleaned_params = {
                k: v[0] if isinstance(v, list) and len(v) == 1 else v
                for k, v in query_params.items()
            }
            # Используем exclude_unset=True для применения значений по умолчанию
            validated = model(**cleaned_params, exclude_unset=True)
            # Преобразуем в словарь и обратно для применения значений по умолчанию
            return model(**validated.model_dump())
        except ValidationError:
            return None


class ResponseValidator:
    """Валидатор ответов с использованием Pydantic"""

    @staticmethod
    def validate_response(
        response_data: Dict[str, Any], model: Type[T]
    ) -> Optional[Response]:
        """Валидация данных ответа"""
        if BaseModel is None or ValidationError is None:
            raise ImportError(
                "pydantic is required for validate_response. "
                "Install it with: pip install pydantic"
            )
        try:
            # Используем exclude_unset=True для применения значений по умолчанию
            validated = model(**response_data, exclude_unset=True)
            # Преобразуем в словарь и обратно для применения значений по умолчанию
            return Response.json(validated.model_dump())
        except ValidationError as e:
            return Response.json(
                {"detail": "Response validation failed", "errors": e.errors()},
                status_code=500,
            )
