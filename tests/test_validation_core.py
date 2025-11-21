from typing import Optional

import pytest

try:
    from pydantic import BaseModel, Field
except ImportError:
    pytest.skip("pydantic not installed", allow_module_level=True)

from qakeapi.core.request import Request
from qakeapi.core.responses import JSONResponse
from qakeapi.validation.interfaces import (
    DataValidator,
    PydanticValidator,
    RequestValidator,
    ResponseValidator,
    ValidationFactory,
)
from qakeapi.validation.models import (
    RequestModel,
    ResponseModel,
    create_model_validator,
    validate_path_params,
    validate_query_params,
    validate_request_body,
    validate_response_model,
)


# Test models
class UserModel(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


class QueryParamsModel(BaseModel):
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=100)


class PathParamsModel(BaseModel):
    user_id: int = Field(ge=1)


# Test validation interfaces
def test_pydantic_validator():
    """Test PydanticValidator implementation"""
    validator = PydanticValidator(UserModel)

    # Test valid data
    valid_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    validated = validator.validate(valid_data)
    assert isinstance(validated, UserModel)
    assert validated.id == 1
    assert validated.name == "John Doe"

    # Test invalid data
    with pytest.raises(Exception):
        validator.validate({"id": "invalid"})


def test_validation_factory():
    """Test ValidationFactory"""
    # Test creating PydanticValidator
    validator = ValidationFactory.create_validator("pydantic", model_class=UserModel)
    assert isinstance(validator, PydanticValidator)

    # Test invalid validator type
    with pytest.raises(ValueError):
        ValidationFactory.create_validator("invalid")

    # Test invalid model class
    class InvalidModel:
        pass

    with pytest.raises(ValueError):
        ValidationFactory.create_validator("pydantic", model_class=InvalidModel)


# Test validation models
@pytest.mark.asyncio
async def test_validate_request_body():
    """Test request body validation decorator"""

    @validate_request_body(UserModel)
    async def handler(request):
        return JSONResponse(request.validated_data.model_dump())

    # Test valid request
    valid_json = b'{"id": 1, "name": "John", "email": "john@example.com"}'
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")],
            "body": valid_json,
        }
    )
    request._body = valid_json  # Set body directly for testing

    response = await handler(request)
    assert response.status_code == 200
    body = await response.body
    assert b"john@example.com" in body

    # Test invalid request
    invalid_json = b'{"id": "invalid"}'
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")],
            "body": invalid_json,
        }
    )
    request._body = invalid_json  # Set body directly for testing

    response = await handler(request)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validate_response_model():
    """Test response model validation decorator"""

    @validate_response_model(UserModel)
    async def handler(request):
        return {"id": 1, "name": "John", "email": "john@example.com"}

    request = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})

    response = await handler(request)
    assert response.status_code == 200
    body = await response.body
    assert b"john@example.com" in body


@pytest.mark.asyncio
async def test_validate_path_params():
    """Test path parameters validation decorator"""

    @validate_path_params(user_id=PathParamsModel)
    async def handler(request):
        return JSONResponse(
            {"user_id": request.validated_path_params["user_id"].user_id}
        )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/users/1",
            "headers": [],
            "path_params": {"user_id": "1"},
        }
    )

    response = await handler(request)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_validate_query_params():
    """Test query parameters validation decorator"""

    @validate_query_params(QueryParamsModel)
    async def handler(request):
        return JSONResponse(request.validated_query_params.model_dump())

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"page=1&limit=10",
        }
    )

    response = await handler(request)
    assert response.status_code == 200


def test_request_response_models():
    """Test RequestModel and ResponseModel"""

    class TestRequestModel(RequestModel):
        name: str
        age: int

    class TestResponseModel(ResponseModel):
        id: int
        name: str

    # Test RequestModel
    with pytest.raises(Exception):
        TestRequestModel(name="John", age=30, extra_field="value")

    # Test ResponseModel
    model = TestResponseModel(id=1, name="John", extra_field="value")
    assert model.id == 1
    assert model.name == "John"


@pytest.mark.asyncio
async def test_create_model_validator():
    """Test combined model validators"""

    @create_model_validator(
        validate_request_body(UserModel), validate_response_model(UserModel)
    )
    async def handler(request):
        return request.validated_data.model_dump()

    valid_json = b'{"id": 1, "name": "John", "email": "john@example.com"}'
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")],
            "body": valid_json,
        }
    )
    request._body = valid_json  # Set body directly for testing

    response = await handler(request)
    assert response.status_code == 200
    body = await response.body
    assert b"john@example.com" in body
