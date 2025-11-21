"""
Демонстрационное приложение QakeAPI
"""
from qakeapi import QakeAPI, Request, JSONResponse, Depends
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware
from qakeapi.core.exceptions import HTTPException
from qakeapi.utils.status import status

# Создаем приложение
app = QakeAPI(
    title="QakeAPI Демонстрация",
    description="Демонстрационное приложение, показывающее возможности QakeAPI фреймворка",
    version="1.0.0",
    debug=True,
)

# Добавляем middleware
app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
))
app.add_middleware(LoggingMiddleware())

# Фиктивная база данных
fake_items_db = [
    {"id": 1, "name": "Ноутбук", "price": 50000.0, "description": "Мощный ноутбук для работы"},
    {"id": 2, "name": "Мышь", "price": 1500.0, "description": "Беспроводная мышь"},
    {"id": 3, "name": "Клавиатура", "price": 5000.0, "description": "Механическая клавиатура"},
]

fake_users_db = [
    {"id": 1, "name": "Алиса", "email": "alice@example.com", "active": True},
    {"id": 2, "name": "Боб", "email": "bob@example.com", "active": True},
    {"id": 3, "name": "Кэрол", "email": "carol@example.com", "active": False},
]


# Зависимости
def get_db():
    """Получить подключение к базе данных (заглушка)"""
    return {"connection": "fake_db_connection"}


def get_current_user(request: Request):
    """Получить текущего пользователя (заглушка)"""
    # В реальном приложении здесь была бы логика аутентификации
    return {"id": 1, "name": "Демо пользователь", "email": "demo@example.com"}


# Маршруты
@app.get("/")
async def root():
    """
    Главная страница API
    
    Возвращает информацию о QakeAPI фреймворке и доступных endpoints.
    """
    return {
        "message": "Добро пожаловать в QakeAPI! 🚀",
        "description": "Мощный асинхронный веб-фреймворк для Python",
        "version": "1.0.0",
        "features": [
            "Асинхронная обработка запросов",
            "Автоматическая валидация данных",
            "Встроенная система middleware",
            "WebSocket поддержка",
            "Dependency Injection",
            "Автоматическая генерация OpenAPI документации"
        ],
        "endpoints": {
            "items": "/items/ - Управление товарами",
            "users": "/users/ - Управление пользователями",
            "health": "/health - Проверка состояния сервиса",
            "docs": "/docs - Swagger UI документация",
            "redoc": "/redoc - ReDoc документация"
        }
    }


@app.get("/health")
async def health_check():
    """
    Проверка состояния сервиса
    
    Возвращает информацию о состоянии приложения и его компонентов.
    """
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        "database": "connected",
        "cache": "available",
        "services": {
            "api": "running",
            "websocket": "available",
            "static_files": "serving"
        }
    }


# Товары
@app.get("/items/")
async def get_items(
    skip: int = 0,
    limit: int = 10,
    search: str = None,
    db: dict = Depends(get_db)
):
    """
    Получить список товаров
    
    - **skip**: количество товаров для пропуска (пагинация)
    - **limit**: максимальное количество товаров для возврата
    - **search**: поисковый запрос по названию товара
    """
    items = fake_items_db.copy()
    
    # Фильтрация по поиску
    if search:
        items = [item for item in items if search.lower() in item["name"].lower()]
    
    # Пагинация
    items = items[skip:skip + limit]
    
    return {
        "items": items,
        "total": len(fake_items_db),
        "skip": skip,
        "limit": limit,
        "search": search
    }


@app.get("/items/{item_id}")
async def get_item(item_id: int, db: dict = Depends(get_db)):
    """
    Получить товар по ID
    
    - **item_id**: уникальный идентификатор товара
    """
    for item in fake_items_db:
        if item["id"] == item_id:
            return item
    
    raise HTTPException(
        status_code=status.NOT_FOUND,
        detail=f"Товар с ID {item_id} не найден"
    )


@app.post("/items/")
async def create_item(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: dict = Depends(get_db)
):
    """
    Создать новый товар
    
    Создает новый товар в системе. Требует аутентификации.
    """
    data = await request.json()
    
    # Валидация данных
    required_fields = ["name", "price"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.BAD_REQUEST,
                detail=f"Поле '{field}' обязательно для заполнения"
            )
    
    if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
        raise HTTPException(
            status_code=status.BAD_REQUEST,
            detail="Цена должна быть положительным числом"
        )
    
    # Создаем новый товар
    new_item = {
        "id": len(fake_items_db) + 1,
        "name": data["name"],
        "price": float(data["price"]),
        "description": data.get("description", ""),
        "created_by": current_user["id"]
    }
    
    fake_items_db.append(new_item)
    
    return {
        "message": "Товар успешно создан",
        "item": new_item
    }


@app.put("/items/{item_id}")
async def update_item(
    item_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: dict = Depends(get_db)
):
    """
    Обновить товар
    
    Обновляет существующий товар. Требует аутентификации.
    """
    # Находим товар
    item_index = None
    for i, item in enumerate(fake_items_db):
        if item["id"] == item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(
            status_code=status.NOT_FOUND,
            detail=f"Товар с ID {item_id} не найден"
        )
    
    data = await request.json()
    
    # Обновляем товар
    if "name" in data:
        fake_items_db[item_index]["name"] = data["name"]
    if "price" in data:
        if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
            raise HTTPException(
                status_code=status.BAD_REQUEST,
                detail="Цена должна быть положительным числом"
            )
        fake_items_db[item_index]["price"] = float(data["price"])
    if "description" in data:
        fake_items_db[item_index]["description"] = data["description"]
    
    fake_items_db[item_index]["updated_by"] = current_user["id"]
    
    return {
        "message": "Товар успешно обновлен",
        "item": fake_items_db[item_index]
    }


@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: dict = Depends(get_db)
):
    """
    Удалить товар
    
    Удаляет товар из системы. Требует аутентификации.
    """
    # Находим товар
    item_index = None
    for i, item in enumerate(fake_items_db):
        if item["id"] == item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(
            status_code=status.NOT_FOUND,
            detail=f"Товар с ID {item_id} не найден"
        )
    
    deleted_item = fake_items_db.pop(item_index)
    
    return {
        "message": "Товар успешно удален",
        "deleted_item": deleted_item
    }


# Пользователи
@app.get("/users/")
async def get_users(
    skip: int = 0,
    limit: int = 10,
    active_only: bool = None,
    db: dict = Depends(get_db)
):
    """
    Получить список пользователей
    
    - **skip**: количество пользователей для пропуска
    - **limit**: максимальное количество пользователей
    - **active_only**: показать только активных пользователей
    """
    users = fake_users_db.copy()
    
    # Фильтрация по активности
    if active_only is not None:
        users = [user for user in users if user["active"] == active_only]
    
    # Пагинация
    users = users[skip:skip + limit]
    
    return {
        "users": users,
        "total": len(fake_users_db),
        "skip": skip,
        "limit": limit,
        "active_only": active_only
    }


@app.get("/users/{user_id}")
async def get_user(user_id: int, db: dict = Depends(get_db)):
    """
    Получить пользователя по ID
    
    - **user_id**: уникальный идентификатор пользователя
    """
    for user in fake_users_db:
        if user["id"] == user_id:
            return user
    
    raise HTTPException(
        status_code=status.NOT_FOUND,
        detail=f"Пользователь с ID {user_id} не найден"
    )


@app.get("/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Получить информацию о текущем пользователе
    
    Возвращает информацию о текущем аутентифицированном пользователе.
    """
    return {
        "user": current_user,
        "permissions": ["read", "write", "delete"],
        "last_login": "2024-01-01T00:00:00Z"
    }


# Статистика
@app.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db: dict = Depends(get_db)
):
    """
    Получить статистику системы
    
    Возвращает общую статистику по товарам и пользователям.
    """
    active_users = len([user for user in fake_users_db if user["active"]])
    total_items_value = sum(item["price"] for item in fake_items_db)
    
    return {
        "users": {
            "total": len(fake_users_db),
            "active": active_users,
            "inactive": len(fake_users_db) - active_users
        },
        "items": {
            "total": len(fake_items_db),
            "total_value": total_items_value,
            "average_price": total_items_value / len(fake_items_db) if fake_items_db else 0
        },
        "system": {
            "uptime": "1 day, 2 hours, 30 minutes",
            "requests_today": 1247,
            "errors_today": 3
        }
    }


# Обработчики событий
@app.on_event("startup")
async def startup():
    """Выполняется при запуске приложения"""
    print("🚀 QakeAPI приложение запускается...")
    print(f"📊 Загружено товаров: {len(fake_items_db)}")
    print(f"👥 Загружено пользователей: {len(fake_users_db)}")
    print("✅ Приложение готово к работе!")


@app.on_event("shutdown")
async def shutdown():
    """Выполняется при завершении работы приложения"""
    print("🛑 QakeAPI приложение завершает работу...")
    print("💾 Сохранение данных...")
    print("✅ Приложение успешно завершено!")


# Обработчики исключений
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Кастомный обработчик 404 ошибок"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Ресурс не найден",
            "message": f"Запрошенный путь '{request.path}' не существует",
            "suggestion": "Проверьте URL или обратитесь к документации API по адресу /docs",
            "available_endpoints": [
                "/",
                "/items/",
                "/users/",
                "/health",
                "/stats"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Кастомный обработчик внутренних ошибок"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "message": "Произошла непредвиденная ошибка. Попробуйте позже.",
            "request_id": f"req_{id(request)}",
            "support": "Если проблема повторяется, обратитесь в поддержку"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print("🌟 Запуск QakeAPI демонстрационного приложения")
    print("📚 Документация доступна по адресу: http://localhost:8000/docs")
    print("🔄 ReDoc документация: http://localhost:8000/redoc")
    print("🌐 Приложение: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
