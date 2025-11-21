"""
Тесты для working_demo.py приложения
"""

import os
import sys
from pathlib import Path

import pytest

# Добавляем путь к examples в sys.path
examples_path = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_path))

try:
    from working_demo import app, items_db
except ImportError:
    pytest.skip("working_demo.py not found", allow_module_level=True)


@pytest.fixture
def client():
    """Создать тестовый клиент для working_demo"""
    from httpx import AsyncClient

    try:
        from httpx import ASGITransport
    except ImportError:
        from httpx._transports.asgi import ASGITransport

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
def reset_items_db():
    """Сбросить базу данных товаров к исходному состоянию"""
    original_items = [
        {"id": 1, "name": "Ноутбук", "price": 50000},
        {"id": 2, "name": "Мышь", "price": 1500},
        {"id": 3, "name": "Клавиатура", "price": 5000},
    ]

    # Очищаем и восстанавливаем исходные данные
    items_db.clear()
    items_db.extend(original_items)

    yield

    # Восстанавливаем после теста
    items_db.clear()
    items_db.extend(original_items)


class TestWorkingDemoBasic:
    """Базовые тесты working_demo приложения"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Тест главной страницы"""
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "QakeAPI Working Demo" in data["message"]
        assert "version" in data
        assert "features" in data
        assert "endpoints" in data

        # Проверяем структуру ответа
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0
        assert isinstance(data["endpoints"], dict)

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Тест endpoint проверки здоровья"""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "items_count" in data
        assert "app" in data
        assert data["app"] == "QakeAPI Working Demo"
        assert isinstance(data["items_count"], int)

    @pytest.mark.asyncio
    async def test_openapi_docs(self, client):
        """Тест доступности OpenAPI документации"""
        # OpenAPI схема
        response = await client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "QakeAPI Working Demo"

        # Swagger UI
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        # ReDoc
        response = await client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestWorkingDemoItems:
    """Тесты работы с товарами"""

    @pytest.mark.asyncio
    async def test_get_items(self, client, reset_items_db):
        """Тест получения списка товаров"""
        response = await client.get("/items")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] == len(data["items"])
        assert data["total"] >= 3  # Исходные товары

        # Проверяем структуру товара
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "name" in item
            assert "price" in item

    @pytest.mark.asyncio
    async def test_get_item_by_id(self, client, reset_items_db):
        """Тест получения товара по ID"""
        # Существующий товар
        response = await client.get("/items/1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "price" in data
        assert data["name"] == "Ноутбук"
        assert data["price"] == 50000

    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, client, reset_items_db):
        """Тест получения несуществующего товара"""
        response = await client.get("/items/999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "999" in data["detail"]
        assert "не найден" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_item_valid(self, client, reset_items_db):
        """Тест создания валидного товара"""
        new_item = {"name": "Новый товар", "price": 1000}

        response = await client.post("/items", json=new_item)
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "item" in data
        assert "успешно создан" in data["message"]

        created_item = data["item"]
        assert created_item["name"] == new_item["name"]
        assert created_item["price"] == new_item["price"]
        assert "id" in created_item
        assert created_item["id"] > 3  # Новый ID больше исходных

    @pytest.mark.asyncio
    async def test_create_item_missing_name(self, client, reset_items_db):
        """Тест создания товара без имени"""
        invalid_item = {
            "price": 1000
            # name отсутствует
        }

        response = await client.post("/items", json=invalid_item)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "name" in data["detail"]
        assert "обязательно" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_item_invalid_price(self, client, reset_items_db):
        """Тест создания товара с невалидной ценой"""
        test_cases = [
            {"name": "Товар", "price": -100},  # Отрицательная цена
            {"name": "Товар", "price": 0},  # Нулевая цена
            {"name": "Товар", "price": "abc"},  # Нечисловая цена
            {"name": "Товар"},  # Отсутствующая цена
        ]

        for invalid_item in test_cases:
            response = await client.post("/items", json=invalid_item)
            assert response.status_code == 400

            data = response.json()
            assert "detail" in data
            assert "price" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_item_empty_name(self, client, reset_items_db):
        """Тест создания товара с пустым именем"""
        invalid_item = {"name": "", "price": 1000}

        response = await client.post("/items", json=invalid_item)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "name" in data["detail"]


class TestWorkingDemoSpecialEndpoints:
    """Тесты специальных endpoints"""

    @pytest.mark.asyncio
    async def test_large_response(self, client):
        """Тест большого ответа"""
        response = await client.get("/large")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 100

        # Проверяем содержимое
        assert data["data"][0] == "Item 0"
        assert data["data"][99] == "Item 99"

    @pytest.mark.asyncio
    async def test_error_demo(self, client):
        """Тест демонстрации ошибки"""
        # В debug режиме ValueError может быть поднят, но обычно обрабатывается как 500
        try:
            response = await client.get("/error")
            # Ошибка может быть обработана как 500 или как исключение
            assert response.status_code in [500, 400]

            data = response.json()
            # Может быть "detail" или "message" в зависимости от обработки
            assert "detail" in data or "message" in data or "error" in data
        except ValueError:
            # В debug режиме ошибка может быть поднята
            pass


class TestWorkingDemoIntegration:
    """Интеграционные тесты"""

    @pytest.mark.asyncio
    async def test_full_item_workflow(self, client, reset_items_db):
        """Тест полного цикла работы с товаром"""
        # 1. Получаем исходное количество товаров
        response = await client.get("/items")
        initial_count = response.json()["total"]

        # 2. Создаем новый товар
        new_item = {"name": "Тестовый товар", "price": 2500}
        response = await client.post("/items", json=new_item)
        assert response.status_code == 200
        created_item = response.json()["item"]

        # 3. Проверяем, что количество товаров увеличилось
        response = await client.get("/items")
        assert response.json()["total"] == initial_count + 1

        # 4. Получаем созданный товар по ID
        response = await client.get(f"/items/{created_item['id']}")
        assert response.status_code == 200
        fetched_item = response.json()

        assert fetched_item["id"] == created_item["id"]
        assert fetched_item["name"] == new_item["name"]
        assert fetched_item["price"] == new_item["price"]

        # 5. Проверяем, что товар есть в общем списке
        response = await client.get("/items")
        items = response.json()["items"]
        item_ids = [item["id"] for item in items]
        assert created_item["id"] in item_ids

    @pytest.mark.asyncio
    async def test_multiple_item_creation(self, client, reset_items_db):
        """Тест создания нескольких товаров"""
        items_to_create = [
            {"name": "Товар 1", "price": 100},
            {"name": "Товар 2", "price": 200},
            {"name": "Товар 3", "price": 300},
        ]

        created_ids = []

        for item_data in items_to_create:
            response = await client.post("/items", json=item_data)
            assert response.status_code == 200
            created_item = response.json()["item"]
            created_ids.append(created_item["id"])

        # Проверяем, что все товары созданы с уникальными ID
        assert len(set(created_ids)) == len(created_ids)

        # Проверяем, что все товары доступны
        for item_id in created_ids:
            response = await client.get(f"/items/{item_id}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_reflects_items_count(self, client, reset_items_db):
        """Тест что health endpoint отражает актуальное количество товаров"""
        # Получаем исходное состояние
        response = await client.get("/health")
        initial_count = response.json()["items_count"]

        # Создаем новый товар
        new_item = {"name": "Товар для теста health", "price": 1500}
        response = await client.post("/items", json=new_item)
        assert response.status_code == 200

        # Проверяем, что health показывает обновленное количество
        response = await client.get("/health")
        updated_count = response.json()["items_count"]
        assert updated_count == initial_count + 1


class TestWorkingDemoErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.mark.asyncio
    async def test_invalid_json(self, client):
        """Тест отправки невалидного JSON"""
        response = await client.post(
            "/items",
            content="invalid json{",
            headers={"content-type": "application/json"},
        )
        # Должна быть ошибка парсинга JSON - может быть 400 или 422
        # В некоторых случаях может быть ValueError, который обрабатывается как 500
        assert response.status_code in [400, 422, 500]

        # Проверяем, что есть сообщение об ошибке
        data = response.json()
        assert "detail" in data or "message" in data or "error" in data

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client):
        """Тест неразрешенного HTTP метода"""
        # PUT не поддерживается для /items
        # Если метод не поддерживается, может быть 404 (маршрут не найден) или 405
        response = await client.put("/items", json={"name": "test", "price": 100})
        assert response.status_code in [404, 405]

    @pytest.mark.asyncio
    async def test_not_found_endpoint(self, client):
        """Тест несуществующего endpoint"""
        response = await client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_item_id_type(self, client):
        """Тест с невалидным типом ID товара"""
        response = await client.get("/items/not-a-number")
        # Должна быть ошибка валидации параметра пути
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
