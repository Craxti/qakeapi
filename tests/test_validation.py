import pytest
from pydantic import BaseModel, Field
from qakeapi.core.responses import Response
from qakeapi.core.validation import (
    DataValidator,
    PydanticValidator,
    ValidationFactory,
    RequestValidator,
    ResponseValidator
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

class TestModel(BaseModel):
    name: str
    age: int
    email: str = None

@pytest.mark.asyncio
async def test_request_body_validation():
    # Валидные данные
    valid_data = {
        "name": "John",
        "age": 30,
        "email": "john@example.com"
    }
    result = await RequestValidator.validate_request_body(valid_data, TestModel)
    assert result is not None
    assert result.name == "John"
    assert result.age == 30
    assert result.email == "john@example.com"
    
    # Невалидные данные
    invalid_data = {
        "name": "John",
        "age": "not_a_number",
        "email": "invalid_email"
    }
    result = await RequestValidator.validate_request_body(invalid_data, TestModel)
    assert result is None

def test_path_params_validation():
    # Валидные данные
    valid_params = {
        "name": "John",
        "age": "30",
        "email": "john@example.com"
    }
    result = RequestValidator.validate_path_params(valid_params, TestModel)
    assert result is not None
    assert result.name == "John"
    assert result.age == 30
    assert result.email == "john@example.com"
    
    # Невалидные данные
    invalid_params = {
        "name": "John",
        "age": "not_a_number",
        "email": "invalid_email"
    }
    result = RequestValidator.validate_path_params(invalid_params, TestModel)
    assert result is None

def test_query_params_validation():
    # Валидные данные
    valid_params = {
        "name": ["John"],
        "age": ["30"],
        "email": ["john@example.com"]
    }
    result = RequestValidator.validate_query_params(valid_params, TestModel)
    assert result is not None
    assert result.name == "John"
    assert result.age == 30
    assert result.email == "john@example.com"
    
    # Невалидные данные
    invalid_params = {
        "name": ["John"],
        "age": ["not_a_number"],
        "email": ["invalid_email"]
    }
    result = RequestValidator.validate_query_params(invalid_params, TestModel)
    assert result is None

def test_response_validation():
    # Валидные данные
    valid_data = {
        "name": "John",
        "age": 30,
        "email": "john@example.com"
    }
    result = ResponseValidator.validate_response(valid_data, TestModel)
    assert isinstance(result, Response)
    assert result.status_code == 200
    
    # Невалидные данные
    invalid_data = {
        "name": "John",
        "age": "not_a_number",
        "email": "invalid_email"
    }
    result = ResponseValidator.validate_response(invalid_data, TestModel)
    assert isinstance(result, Response)
    assert result.status_code == 500 