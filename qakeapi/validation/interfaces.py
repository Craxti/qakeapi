from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


class DataValidator(ABC):
    """Base interface for data validation"""

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Any:
        """Data validation"""
        pass


class RequestValidator(DataValidator):
    """Interface for request validation"""

    @abstractmethod
    def validate_query_params(self, params: Dict[str, Any]) -> Any:
        """Query parameters validation"""
        pass

    @abstractmethod
    def validate_path_params(self, params: Dict[str, Any]) -> Any:
        """Path parameters validation"""
        pass

    @abstractmethod
    def validate_body(self, body: Dict[str, Any]) -> Any:
        """Request body validation"""
        pass


class ResponseValidator(DataValidator):
    """Interface for response validation"""

    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> Any:
        """Response validation"""
        pass


class PydanticValidator(RequestValidator, ResponseValidator):
    """Pydantic-based validator implementation"""

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
    """Factory for creating validators"""

    @staticmethod
    def create_validator(validator_type: str, **kwargs: Any) -> DataValidator:
        """Creates validator of specified type"""
        if validator_type == "pydantic":
            try:
                from pydantic import BaseModel

                if not issubclass(kwargs.get("model_class", type), BaseModel):
                    raise ValueError("model_class must be a subclass of BaseModel")
                return PydanticValidator(kwargs["model_class"])
            except ImportError:
                raise ImportError(
                    "pydantic must be installed to use PydanticValidator"
                )
        raise ValueError(f"Unknown validator type: {validator_type}")
