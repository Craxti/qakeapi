from typing import Any, Dict, Type, TypeVar, Optional
from pydantic import BaseModel

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
    
    def __init__(self, model_class: Type[BaseModel]):
        if not issubclass(model_class, BaseModel):
            raise TypeError("model_class must be a Pydantic model")
        self.model_class = model_class
        
    def validate(self, data: Dict[str, Any]) -> BaseModel:
        """Validate data against Pydantic model"""
        return self.model_class(**data)

class ValidationFactory:
    """Factory for creating validators"""
    
    VALIDATORS = {
        "data": DataValidator,
        "pydantic": PydanticValidator
    }
    
    @classmethod
    def create(cls, validator_type: str, model_class: Optional[Type[BaseModel]] = None) -> Any:
        """Create validator instance"""
        if validator_type not in cls.VALIDATORS:
            raise ValueError(f"Unknown validator type: {validator_type}")
            
        validator_class = cls.VALIDATORS[validator_type]
        
        if validator_type == "pydantic":
            if not model_class:
                raise ValueError("model_class is required for pydantic validator")
            return validator_class(model_class)
            
        return validator_class() 