"""
Демонстрационное приложение для тестирования API эндпоинтов
"""
import asyncio
import json
from qakeapi import QakeAPI, Request, JSONResponse, HTTPException
from qakeapi.utils.validation import DataValidator, StringValidator, IntegerValidator
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware

# Создаем приложение
app = QakeAPI(
    title="Demo API",
    description="Демонстрационное API для тестирования",
    version="1.0.0",
    debug=True
)

# Добавляем middleware
app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
))

# Простая база данных в памяти
users_db = [
    {"id": 1, "name": "Алексей", "email": "alex@example.com", "age": 30},
    {"id": 2, "name": "Мария", "email": "maria@example.com", "age": 25},
]

items_db = [
    {"id": 1, "title": "Ноутбук", "price": 50000, "category": "electronics"},
    {"id": 2, "title": "Книга", "price": 500, "category": "books"},
]

next_user_id = 3
next_item_id = 3

# Валидаторы
user_validator = DataValidator({
    "name": StringValidator(min_length=2, max_length=50),
    "email": StringValidator(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$'),
    "age": IntegerValidator(min_value=0, max_value=150, required=False),
})

item_validator = DataValidator({
    "title": StringValidator(min_length=1, max_length=100),
    "price": IntegerValidator(min_value=0),
    "category": StringValidator(max_length=50, required=False),
})

# === БАЗОВЫЕ МАРШРУТЫ ===

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Добро пожаловать в Demo API!",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "items": "/items",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "users_count": len(users_db),
        "items_count": len(items_db)
    }

# === ПОЛЬЗОВАТЕЛИ ===

@app.get("/users")
async def get_users(limit: int = 10, offset: int = 0):
    """Получить список пользователей"""
    start = offset
    end = offset + limit
    paginated_users = users_db[start:end]
    
    return {
        "users": paginated_users,
        "total": len(users_db),
        "limit": limit,
        "offset": offset
    }

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Получить пользователя по ID"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID")
    
    for user in users_db:
        if user["id"] == user_id_int:
            return {"user": user}
    
    raise HTTPException(status_code=404, detail="Пользователь не найден")

@app.post("/users")
async def create_user(request: Request):
    """Создать нового пользователя"""
    data = await request.json()
    
    # Валидация
    result = user_validator.validate(data)
    if not result.is_valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})
    
    # Проверка уникальности email
    for user in users_db:
        if user["email"] == result.data["email"]:
            raise HTTPException(status_code=409, detail="Email уже используется")
    
    # Создание пользователя
    global next_user_id
    user = {"id": next_user_id, **result.data}
    users_db.append(user)
    next_user_id += 1
    
    return {"user": user, "message": "Пользователь создан"}

@app.put("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    """Обновить пользователя"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID")
    
    data = await request.json()
    result = user_validator.validate(data)
    if not result.is_valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})
    
    for i, user in enumerate(users_db):
        if user["id"] == user_id_int:
            users_db[i] = {"id": user_id_int, **result.data}
            return {"user": users_db[i], "message": "Пользователь обновлен"}
    
    raise HTTPException(status_code=404, detail="Пользователь не найден")

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Удалить пользователя"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID")
    
    for i, user in enumerate(users_db):
        if user["id"] == user_id_int:
            deleted_user = users_db.pop(i)
            return {"message": "Пользователь удален", "user": deleted_user}
    
    raise HTTPException(status_code=404, detail="Пользователь не найден")

# === ТОВАРЫ ===

@app.get("/items")
async def get_items(category: str = None, min_price: int = None, max_price: int = None):
    """Получить список товаров с фильтрацией"""
    filtered_items = items_db.copy()
    
    if category:
        filtered_items = [item for item in filtered_items if item.get("category") == category]
    
    if min_price is not None:
        filtered_items = [item for item in filtered_items if item.get("price", 0) >= min_price]
    
    if max_price is not None:
        filtered_items = [item for item in filtered_items if item.get("price", 0) <= max_price]
    
    return {
        "items": filtered_items,
        "total": len(filtered_items),
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        }
    }

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    """Получить товар по ID"""
    try:
        item_id_int = int(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID")
    
    for item in items_db:
        if item["id"] == item_id_int:
            return {"item": item}
    
    raise HTTPException(status_code=404, detail="Товар не найден")

@app.post("/items")
async def create_item(request: Request):
    """Создать новый товар"""
    data = await request.json()
    
    result = item_validator.validate(data)
    if not result.is_valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})
    
    global next_item_id
    item = {"id": next_item_id, **result.data}
    items_db.append(item)
    next_item_id += 1
    
    return {"item": item, "message": "Товар создан"}

# === ПОИСК ===

@app.get("/search")
async def search(q: str, type: str = "all"):
    """Поиск по пользователям и товарам"""
    results = {"users": [], "items": []}
    
    if type in ["all", "users"]:
        results["users"] = [
            user for user in users_db
            if q.lower() in user["name"].lower() or q.lower() in user["email"].lower()
        ]
    
    if type in ["all", "items"]:
        results["items"] = [
            item for item in items_db
            if q.lower() in item["title"].lower()
        ]
    
    return {
        "query": q,
        "type": type,
        "results": results,
        "total": len(results["users"]) + len(results["items"])
    }

# === ДЕМО ЭНДПОИНТЫ ===

@app.get("/demo/error")
async def demo_error():
    """Демонстрация обработки ошибок"""
    raise HTTPException(status_code=500, detail="Это демонстрационная ошибка")

@app.get("/demo/validation")
async def demo_validation(name: str = None, age: int = None):
    """Демонстрация валидации параметров"""
    if not name:
        raise HTTPException(status_code=400, detail="Параметр 'name' обязателен")
    
    if age is not None and (age < 0 or age > 150):
        raise HTTPException(status_code=400, detail="Возраст должен быть от 0 до 150")
    
    return {
        "message": "Валидация прошла успешно",
        "data": {"name": name, "age": age}
    }

@app.post("/demo/echo")
async def demo_echo(request: Request):
    """Эхо сервис - возвращает отправленные данные"""
    data = await request.json()
    return {
        "echo": data,
        "method": request.method,
        "path": request.path,
        "headers": dict(request.headers)
    }

if __name__ == "__main__":
    print("Demo API запущен!")
    print("Доступные эндпоинты:")
    print("  GET  / - Главная страница")
    print("  GET  /health - Проверка здоровья")
    print("  GET  /users - Список пользователей")
    print("  POST /users - Создать пользователя")
    print("  GET  /users/{id} - Получить пользователя")
    print("  GET  /items - Список товаров")
    print("  POST /items - Создать товар")
    print("  GET  /search?q=query - Поиск")
    print("  GET  /docs - Swagger UI")
    print("")
    print("Для запуска сервера используйте:")
    print("  uvicorn test_api_demo:app --reload")
    
    # Проверяем, что все работает
    print(f"Зарегистрировано маршрутов: {len(app.routes)}")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"  {route.methods} {route.path}")
