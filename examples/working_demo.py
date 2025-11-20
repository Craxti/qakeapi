"""
Рабочая демонстрация QakeAPI с основными улучшениями
"""
from qakeapi import QakeAPI, Request, JSONResponse
from qakeapi.core.exceptions import HTTPException
from qakeapi.utils.status import status

# Создаем приложение
app = QakeAPI(
    title="QakeAPI Working Demo",
    version="1.0.0",
    description="Рабочая демонстрация основных возможностей QakeAPI",
    debug=True,
)

# Простая база данных
items_db = [
    {"id": 1, "name": "Ноутбук", "price": 50000},
    {"id": 2, "name": "Мышь", "price": 1500},
    {"id": 3, "name": "Клавиатура", "price": 5000},
]


@app.get("/")
async def root():
    """Главная страница"""
    return {
        "message": "Добро пожаловать в QakeAPI Working Demo!",
        "version": "1.0.0",
        "features": [
            "Базовая маршрутизация",
            "Валидация параметров",
            "Обработка ошибок",
            "JSON ответы",
            "OpenAPI документация",
        ],
        "endpoints": {
            "items": "/items - список товаров",
            "item": "/items/{id} - товар по ID",
            "create": "POST /items - создать товар",
            "docs": "/docs - документация",
        },
    }


@app.get("/health")
async def health():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "items_count": len(items_db),
        "app": "QakeAPI Working Demo",
    }


@app.get("/items")
async def get_items():
    """Получить все товары"""
    return {"items": items_db, "total": len(items_db)}


@app.get("/items/{item_id}")
async def get_item(item_id: str):
    """Получить товар по ID"""
    try:
        item_id_int = int(item_id)
    except ValueError:
        raise HTTPException(status.BAD_REQUEST, f"Неверный формат ID: {item_id}")

    for item in items_db:
        if item["id"] == item_id_int:
            return item

    raise HTTPException(status.NOT_FOUND, f"Товар с ID {item_id} не найден")


@app.post("/items")
async def create_item(request: Request):
    """Создать новый товар"""
    data = await request.json()

    # Валидация
    if not data.get("name"):
        raise HTTPException(status.BAD_REQUEST, "Поле 'name' обязательно")

    if not isinstance(data.get("price"), (int, float)) or data["price"] <= 0:
        raise HTTPException(
            status.BAD_REQUEST, "Поле 'price' должно быть положительным числом"
        )

    # Создаем товар
    new_id = max(item["id"] for item in items_db) + 1
    new_item = {"id": new_id, "name": data["name"], "price": data["price"]}
    items_db.append(new_item)

    return {"message": "Товар успешно создан", "item": new_item}


@app.get("/large")
async def large_response():
    """Большой ответ"""
    return {
        "message": "Большой ответ для тестирования",
        "data": [f"Item {i}" for i in range(100)],
    }


@app.get("/error")
async def error_demo():
    """Демонстрация ошибки"""
    raise ValueError("Это тестовая ошибка")


# События
@app.on_event("startup")
async def startup():
    print("Запуск QakeAPI Working Demo...")
    print(f"Товаров в базе: {len(items_db)}")


@app.on_event("shutdown")
async def shutdown():
    print("Завершение работы...")


if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("QakeAPI Working Demo")
    print("=" * 50)
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
