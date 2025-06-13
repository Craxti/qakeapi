from typing import Optional

from pydantic import BaseModel, Field
from qakeapi.core.openapi import OpenAPIGenerator, OpenAPIInfo, OpenAPIPath


class TestRequestModel(BaseModel):
    name: str
    age: int
    email: Optional[str] = None


class TestResponseModel(BaseModel):
    id: int
    name: str
    status: str


def test_openapi_info():
    """Тест создания OpenAPI информации"""
    info = OpenAPIInfo(
        title="Test API", version="1.0.0", description="Test Description"
    )
    assert info.title == "Test API"
    assert info.version == "1.0.0"
    assert info.description == "Test Description"


def test_openapi_path():
    """Тест создания OpenAPI пути"""
    path = OpenAPIPath(
        path="/test",
        method="GET",
        summary="Test endpoint",
        description="Test endpoint description",
        request_model=TestRequestModel,
        response_model=TestResponseModel,
        tags=["test"],
    )

    assert path.path == "/test"
    assert path.method == "GET"
    assert path.summary == "Test endpoint"
    assert path.description == "Test endpoint description"
    assert path.request_model == TestRequestModel
    assert path.response_model == TestResponseModel
    assert path.tags == ["test"]


def test_openapi_generator():
    """Тест генерации OpenAPI спецификации"""
    info = OpenAPIInfo(
        title="Test API", version="1.0.0", description="Test Description"
    )
    generator = OpenAPIGenerator(info)

    # Добавляем тестовый путь
    path = OpenAPIPath(
        path="/users",
        method="POST",
        summary="Create user",
        description="Create a new user",
        request_model=TestRequestModel,
        response_model=TestResponseModel,
        tags=["users"],
    )
    generator.add_path(path)

    # Генерируем спецификацию
    spec = generator.generate()

    # Проверяем базовую информацию
    assert spec["openapi"] == "3.0.0"
    assert spec["info"]["title"] == "Test API"
    assert spec["info"]["version"] == "1.0.0"

    # Проверяем путь
    assert "/users" in spec["paths"]
    path_spec = spec["paths"]["/users"]["post"]
    assert path_spec["summary"] == "Create user"
    assert path_spec["description"] == "Create a new user"
    assert path_spec["tags"] == ["users"]

    # Проверяем схему запроса
    request_schema = path_spec["requestBody"]["content"]["application/json"]["schema"]
    assert request_schema["type"] == "object"
    assert "name" in request_schema["properties"]
    assert "age" in request_schema["properties"]
    assert "email" in request_schema["properties"]

    # Проверяем схему ответа
    response_schema = path_spec["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert response_schema["type"] == "object"
    assert "id" in response_schema["properties"]
    assert "name" in response_schema["properties"]
    assert "status" in response_schema["properties"]


def test_swagger_ui_html():
    """Тест генерации HTML для Swagger UI"""
    from qakeapi.core.openapi import get_swagger_ui_html

    html = get_swagger_ui_html(openapi_url="/openapi.json", title="Test API")

    assert "<!DOCTYPE html>" in html
    assert "swagger-ui-bundle.js" in html
    assert "swagger-ui.css" in html
