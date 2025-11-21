"""
Упрощенная демонстрация QakeAPI без сложных зависимостей
"""

from qakeapi import QakeAPI, Request, JSONResponse
from qakeapi.middleware.compression import CompressionMiddleware
from qakeapi.caching.middleware import CacheMiddleware
from qakeapi.caching.cache import CacheManager
from qakeapi.core.exceptions import HTTPException
from qakeapi.utils.status import status

# Создаем приложение
app = QakeAPI(
    title="QakeAPI Simple Demo",
    version="1.0.0",
    description="Простая демонстрация основных возможностей QakeAPI",
    debug=True,
)

# Добавляем middleware
cache_manager = CacheManager()
app.add_middleware(CompressionMiddleware(minimum_size=100))
app.add_middleware(CacheMiddleware(cache_manager=cache_manager, default_expire=60))

# Простая "база данных"
items_db = [
    {"id": 1, "name": "Ноутбук", "price": 50000},
    {"id": 2, "name": "Мышь", "price": 1500},
    {"id": 3, "name": "Клавиатура", "price": 5000},
]


@app.get("/")
async def root():
    """Главная страница"""
    return {
        "message": "Добро пожаловать в QakeAPI Simple Demo!",
        "version": "1.0.0",
        "features": [
            "Автоматическое сжатие ответов",
            "Кеширование данных",
            "Валидация запросов",
            "Обработка ошибок",
            "OpenAPI документация",
        ],
        "endpoints": {
            "items": "/items - список товаров (кешируется)",
            "large": "/large - большой ответ (сжимается)",
            "error": "/error - демонстрация ошибок",
            "docs": "/docs - документация API",
        },
    }


@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "cache_stats": cache_manager.get_stats(),
        "items_count": len(items_db),
    }


@app.get("/items")
async def get_items():
    """Получить список товаров (кешируется)"""
    return {"items": items_db, "total": len(items_db), "cached": True}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Получить товар по ID"""
    for item in items_db:
        if item["id"] == item_id:
            return item

    raise HTTPException(status.NOT_FOUND, f"Товар с ID {item_id} не найден")


@app.post("/items")
async def create_item(request: Request):
    """Создать новый товар"""
    data = await request.json()

    # Простая валидация
    if not data.get("name"):
        raise HTTPException(status.BAD_REQUEST, "Поле 'name' обязательно")

    if not isinstance(data.get("price"), (int, float)) or data["price"] <= 0:
        raise HTTPException(
            status.BAD_REQUEST, "Поле 'price' должно быть положительным числом"
        )

    # Создаем новый товар
    new_id = max(item["id"] for item in items_db) + 1
    new_item = {"id": new_id, "name": data["name"], "price": data["price"]}
    items_db.append(new_item)

    return {"message": "Товар успешно создан", "item": new_item}


@app.get("/large")
async def large_response():
    """Большой ответ для демонстрации сжатия"""
    return {
        "message": "Этот ответ содержит много данных для демонстрации сжатия",
        "data": [
            {
                "id": i,
                "title": f"Элемент номер {i}",
                "description": f"Подробное описание элемента {i} с большим количеством текста "
                * 5,
                "tags": [f"tag{j}" for j in range(10)],
            }
            for i in range(50)
        ],
    }


@app.get("/error")
async def error_demo():
    """Демонстрация обработки ошибок"""
    raise ValueError("Это демонстрационная ошибка")


@app.get("/cache-test")
async def cache_test():
    """Тест кеширования с timestamp"""
    import time

    return {
        "message": "Этот ответ кешируется",
        "timestamp": time.time(),
        "cache_info": "Если timestamp одинаковый - ответ из кеша",
    }


# События жизненного цикла
@app.on_event("startup")
async def startup():
    print("Запуск QakeAPI Simple Demo...")
    print(f"Товаров в базе: {len(items_db)}")
    print("Кеш инициализирован")


@app.on_event("shutdown")
async def shutdown():
    print("Завершение работы...")
    await cache_manager.clear()


if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("QakeAPI Simple Demo")
    print("=" * 50)
    print("Документация: http://localhost:8000/docs")
    print("Тестирование: http://localhost:8000/")
    print("=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
