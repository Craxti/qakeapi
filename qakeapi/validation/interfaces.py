from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


class DataValidator(ABC):
    """Базовый интерфейс для валидации данных"""

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Any:
        """Валидация данных"""
        pass


class RequestValidator(DataValidator):
    """Интерфейс для валидации запросов"""

    @abstractmethod
    def validate_query_params(self, params: Dict[str, Any]) -> Any:
        """Валидация query-параметров"""
        pass

    @abstractmethod
    def validate_path_params(self, params: Dict[str, Any]) -> Any:
        """Валидация path-параметров"""
        pass

    @abstractmethod
    def validate_body(self, body: Dict[str, Any]) -> Any:
        """Валидация тела запроса"""
        pass


class ResponseValidator(DataValidator):
    """Интерфейс для валидации ответов"""

    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> Any:
        """Валидация ответа"""
        pass


class PydanticValidator(RequestValidator, ResponseValidator):
    """Реализация валидатора с использованием Pydantic"""

    def __init__(self, model_class: Type[Any]):
        self.model_class = model_class

    def validate(self, data: Dict[str, Any]) -> Any:
        return self.model_class(**data)

    def validate_query_params(self, params: Dict[str, Any]) -> Any:
        return self.validate(params)

    def validate_path_params(self, params: Dict[str, Any]) -> Any:
        return self.validate(params)

    def validate_body(self, body: Dict[str, Any]) -> Any:
        return self.validate(body)

    def validate_response(self, response: Dict[str, Any]) -> Any:
        return self.validate(response)


class ValidationFactory:
    """Фабрика для создания валидаторов"""

    @staticmethod
    def create_validator(validator_type: str, **kwargs: Any) -> DataValidator:
        """Создает валидатор указанного типа"""
        if validator_type == "pydantic":
            try:
                from pydantic import BaseModel

                if not issubclass(kwargs.get("model_class", type), BaseModel):
                    raise ValueError("model_class должен быть подклассом BaseModel")
                return PydanticValidator(kwargs["model_class"])
            except ImportError:
                raise ImportError(
                    "Для использования PydanticValidator необходимо установить pydantic"
                )
        raise ValueError(f"Неизвестный тип валидатора: {validator_type}")
