import pytest
from pydantic import BaseModel, Field
from qakeapi.core.responses import Response
from qakeapi.core.validation import (
    DataValidator,
    PydanticValidator,
    ValidationFactory
)

class TestDataValidator:
    def test_simple_validator(self):
        validator = DataValidator()
        data = {"name": "John", "age": 30}
        result = validator.validate(data)
        assert result == data
        
    def test_invalid_data(self):
        validator = DataValidator()
        with pytest.raises(ValueError):
            validator.validate(None)

class UserModel(BaseModel):
    name: str = Field(..., min_length=3)
    age: int = Field(..., ge=0, le=120)

class TestPydanticValidator:
    def test_pydantic_validator_creation(self):
        validator = PydanticValidator(UserModel)
        data = {"name": "John", "age": 30}
        result = validator.validate(data)
        assert isinstance(result, UserModel)
        assert result.name == "John"
        assert result.age == 30
        
    def test_invalid_pydantic_data(self):
        validator = PydanticValidator(UserModel)
        with pytest.raises(ValueError):
            validator.validate({"name": "Jo", "age": -1})

class TestValidationFactory:
    def test_unknown_validator_type(self):
        with pytest.raises(ValueError):
            ValidationFactory.create("unknown", UserModel)
            
    def test_invalid_pydantic_model(self):
        with pytest.raises(TypeError):
            ValidationFactory.create("pydantic", dict) 