import pytest
from typing import Any, Dict
from qakeapi.validation.interfaces import (
    DataValidator,
    RequestValidator,
    ResponseValidator,
    ValidationFactory
)

class SimpleValidator(DataValidator):
    """Простой валидатор для тестирования"""
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        return data

class TestDataValidator:
    def test_simple_validator(self):
        validator = SimpleValidator()
        data = {"key": "value"}
        assert validator.validate(data) == data
        
    def test_invalid_data(self):
        validator = SimpleValidator()
        with pytest.raises(ValueError):
            validator.validate("not a dict")

@pytest.mark.asyncio
class TestPydanticValidator:
    async def test_pydantic_validator_creation(self):
        try:
            from pydantic import BaseModel
            
            class TestModel(BaseModel):
                name: str
                age: int
                
            validator = ValidationFactory.create_validator(
                "pydantic",
                model_class=TestModel
            )
            
            data = {"name": "Test", "age": 25}
            validated = validator.validate(data)
            assert validated.name == "Test"
            assert validated.age == 25
            
        except ImportError:
            pytest.skip("Pydantic not installed")
            
    async def test_invalid_pydantic_data(self):
        try:
            from pydantic import BaseModel
            
            class TestModel(BaseModel):
                name: str
                age: int
                
            validator = ValidationFactory.create_validator(
                "pydantic",
                model_class=TestModel
            )
            
            with pytest.raises(Exception):
                validator.validate({"name": "Test", "age": "not an int"})
                
        except ImportError:
            pytest.skip("Pydantic not installed")

class TestValidationFactory:
    def test_unknown_validator_type(self):
        with pytest.raises(ValueError):
            ValidationFactory.create_validator("unknown")
            
    def test_invalid_pydantic_model(self):
        class NotAPydanticModel:
            pass
            
        with pytest.raises(ValueError):
            ValidationFactory.create_validator(
                "pydantic",
                model_class=NotAPydanticModel
            ) 