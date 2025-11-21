"""
Полнофункциональная демонстрация всех возможностей QakeAPI
"""

import asyncio

from qakeapi import (
    CacheManager,
    CacheMiddleware,
    CompressionMiddleware,
    CORSMiddleware,
    DataValidator,
    DiskSpaceHealthCheck,
    ErrorHandler,
    HealthChecker,
    HealthCheckMiddleware,
    IntegerValidator,
    JSONResponse,
    LoggingMiddleware,
    MemoryHealthCheck,
    MetricsCollector,
    MetricsMiddleware,
    QakeAPI,
    RateLimiter,
    RateLimitMiddleware,
    Request,
    StaticFiles,
    StringValidator,
    TemplateRenderer,
    create_error_handler,
    create_metrics_endpoint,
    status,
)

# Создаем приложение с расширенными возможностями
app = QakeAPI(
    title="QakeAPI Enhanced Demo",
    description="Демонстрация всех возможностей QakeAPI",
    version="1.0.0",
    debug=True,
)

# === MIDDLEWARE ===

# CORS
app.add_middleware(
    CORSMiddleware(
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
)

# Сжатие
app.add_middleware(CompressionMiddleware(minimum_size=1000, compression_level=6))

# Логирование
app.add_middleware(
    LoggingMiddleware(log_request_body=True, log_response_body=True, max_body_size=1024)
)

# Метрики
metrics_collector = MetricsCollector()
app.add_middleware(
    MetricsMiddleware(
        collector=metrics_collector, exclude_paths=["/metrics", "/health", "/static"]
    )
)

# Rate Limiting
rate_limiter = RateLimiter(requests_per_minute=100, burst_size=10)
app.add_middleware(RateLimitMiddleware(rate_limiter))

# Кэширование
cache_manager = CacheManager()
app.add_middleware(
    CacheMiddleware(
        cache_manager=cache_manager, default_ttl=300, cache_control_header=True
    )
)

# === HEALTH CHECKS ===

health_checker = HealthChecker()
health_checker.add_check(DiskSpaceHealthCheck(min_free_percent=10.0))
health_checker.add_check(MemoryHealthCheck(max_usage_percent=90.0))

app.add_middleware(
    HealthCheckMiddleware(
        health_checker=health_checker,
        health_path="/health",
        readiness_path="/ready",
        liveness_path="/live",
    )
)

# === ОБРАБОТКА ОШИБОК ===

error_handler = create_error_handler(
    debug=True, log_request_body=True, include_error_id=True
)


# Кастомный обработчик для 404
@error_handler.add_exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        content={
            "error": "Страница не найдена",
            "message": "Проверьте правильность URL",
            "available_endpoints": [
                "/",
                "/api/users",
                "/api/items",
                "/metrics",
                "/health",
                "/docs",
            ],
        },
        status_code=404,
    )


# === СТАТИКА И ШАБЛОНЫ ===

# Статические файлы
app.mount("/static", StaticFiles(directory="static"))

# Шаблоны
templates = TemplateRenderer(directory="templates")

# === ВАЛИДАЦИЯ ===

user_validator = DataValidator(
    {
        "name": StringValidator(min_length=2, max_length=50),
        "email": StringValidator(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"),
        "age": IntegerValidator(min_value=0, max_value=150, required=False),
    }
)

item_validator = DataValidator(
    {
        "title": StringValidator(min_length=1, max_length=100),
        "description": StringValidator(max_length=500, required=False),
        "price": IntegerValidator(min_value=0, required=False),
        "category": StringValidator(max_length=50, required=False),
    }
)

# === БАЗЫ ДАННЫХ (в памяти для демо) ===

users_db = [
    {"id": 1, "name": "Алексей", "email": "alex@example.com", "age": 30},
    {"id": 2, "name": "Мария", "email": "maria@example.com", "age": 25},
]

items_db = [
    {
        "id": 1,
        "title": "Ноутбук",
        "description": "Мощный ноутбук",
        "price": 50000,
        "category": "electronics",
    },
    {
        "id": 2,
        "title": "Книга",
        "description": "Интересная книга",
        "price": 500,
        "category": "books",
    },
]

next_user_id = 3
next_item_id = 3

# === МАРШРУТЫ ===


@app.get("/")
async def home():
    """Главная страница"""
    return templates.render(
        "enhanced_demo.html",
        {
            "title": "QakeAPI Enhanced Demo",
            "features": [
                "🚀 Асинхронная обработка",
                "📊 Встроенные метрики",
                "🛡️ Rate limiting",
                "💾 Кэширование",
                "🏥 Health checks",
                "🔧 Middleware система",
                "📝 Валидация данных",
                "🎯 Обработка ошибок",
            ],
        },
    )


# === API ПОЛЬЗОВАТЕЛЕЙ ===


@app.get("/api/users")
async def get_users(page: int = 1, limit: int = 10):
    """Получить список пользователей с пагинацией"""
    # Увеличиваем кастомную метрику
    metrics_collector.increment_counter("users_list_requests")

    start = (page - 1) * limit
    end = start + limit

    paginated_users = users_db[start:end]

    return {
        "users": paginated_users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(users_db),
            "has_next": end < len(users_db),
        },
    }


@app.post("/api/users")
async def create_user(request: Request):
    """Создать нового пользователя"""
    data = await request.json()

    # Валидация
    validation_result = user_validator.validate(data)
    if not validation_result.is_valid:
        return JSONResponse(
            content={"errors": validation_result.errors}, status_code=status.BAD_REQUEST
        )

    # Проверка уникальности email
    for user in users_db:
        if user["email"] == validation_result.data["email"]:
            return JSONResponse(
                content={"error": "Пользователь с таким email уже существует"},
                status_code=status.CONFLICT,
            )

    # Создание пользователя
    global next_user_id
    user = {"id": next_user_id, **validation_result.data}
    users_db.append(user)
    next_user_id += 1

    # Метрика
    metrics_collector.increment_counter("users_created")

    return {"user": user, "message": "Пользователь создан успешно"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Получить пользователя по ID"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        return JSONResponse(
            content={"error": "Неверный формат ID"}, status_code=status.BAD_REQUEST
        )

    for user in users_db:
        if user["id"] == user_id_int:
            return {"user": user}

    return JSONResponse(
        content={"error": "Пользователь не найден"}, status_code=status.NOT_FOUND
    )


# === API ТОВАРОВ ===


@app.get("/api/items")
async def get_items(category: str = None, min_price: int = None, max_price: int = None):
    """Получить список товаров с фильтрацией"""
    filtered_items = items_db.copy()

    # Фильтрация по категории
    if category:
        filtered_items = [
            item for item in filtered_items if item.get("category") == category
        ]

    # Фильтрация по цене
    if min_price is not None:
        filtered_items = [
            item for item in filtered_items if item.get("price", 0) >= min_price
        ]

    if max_price is not None:
        filtered_items = [
            item for item in filtered_items if item.get("price", 0) <= max_price
        ]

    return {
        "items": filtered_items,
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
        },
        "total": len(filtered_items),
    }


@app.post("/api/items")
async def create_item(request: Request):
    """Создать новый товар"""
    data = await request.json()

    # Валидация
    validation_result = item_validator.validate(data)
    if not validation_result.is_valid:
        return JSONResponse(
            content={"errors": validation_result.errors}, status_code=status.BAD_REQUEST
        )

    # Создание товара
    global next_item_id
    item = {"id": next_item_id, **validation_result.data}
    items_db.append(item)
    next_item_id += 1

    # Метрика
    metrics_collector.increment_counter("items_created")

    return {"item": item, "message": "Товар создан успешно"}


# === СПЕЦИАЛЬНЫЕ ЭНДПОИНТЫ ===


@app.get("/api/search")
async def search(q: str, type: str = "all"):
    """Поиск по пользователям и товарам"""
    results = {"users": [], "items": []}

    if type in ["all", "users"]:
        results["users"] = [
            user
            for user in users_db
            if q.lower() in user["name"].lower() or q.lower() in user["email"].lower()
        ]

    if type in ["all", "items"]:
        results["items"] = [
            item
            for item in items_db
            if q.lower() in item["title"].lower()
            or q.lower() in item.get("description", "").lower()
        ]

    return {
        "query": q,
        "type": type,
        "results": results,
        "total": len(results["users"]) + len(results["items"]),
    }


@app.get("/api/stats")
async def get_stats():
    """Получить статистику приложения"""
    return {
        "users": {"total": len(users_db), "latest": users_db[-1] if users_db else None},
        "items": {
            "total": len(items_db),
            "categories": list(
                set(item.get("category", "unknown") for item in items_db)
            ),
        },
        "system": {
            "cache_stats": cache_manager.get_stats(),
            "health": await health_checker.check_all(),
        },
    }


# === МЕТРИКИ И МОНИТОРИНГ ===

# Эндпоинт метрик
metrics_endpoint = create_metrics_endpoint(metrics_collector)
app.get("/metrics")(metrics_endpoint)

# Prometheus метрики
from qakeapi.monitoring.metrics import create_prometheus_endpoint

prometheus_endpoint = create_prometheus_endpoint(metrics_collector)


@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Метрики в формате Prometheus"""
    return await prometheus_endpoint()


# === ДЕМО ЭНДПОИНТЫ ===


@app.get("/demo/cache")
async def demo_cache():
    """Демонстрация кэширования"""
    import time

    # Этот ответ будет закэширован
    return {
        "message": "Этот ответ кэшируется на 5 минут",
        "timestamp": time.time(),
        "cache_info": "Первый запрос медленный, последующие быстрые",
    }


@app.get("/demo/error")
async def demo_error():
    """Демонстрация обработки ошибок"""
    raise ValueError("Это демонстрационная ошибка для тестирования error handler")


@app.get("/demo/rate-limit")
async def demo_rate_limit():
    """Демонстрация rate limiting"""
    return {
        "message": "Этот эндпоинт ограничен rate limiter",
        "info": "Попробуйте сделать много запросов подряд",
    }


# === STARTUP/SHUTDOWN ===


@app.on_event("startup")
async def startup():
    """Инициализация при запуске"""
    print("🚀 QakeAPI Enhanced Demo запущен!")
    print("📊 Метрики: http://localhost:8000/metrics")
    print("🏥 Health: http://localhost:8000/health")
    print("📚 Docs: http://localhost:8000/docs")

    # Инициализация компонентов
    await cache_manager.initialize()

    # Добавляем начальные метрики
    metrics_collector.set_gauge("app_startup_timestamp", time.time())


@app.on_event("shutdown")
async def shutdown():
    """Очистка при остановке"""
    print("👋 QakeAPI Enhanced Demo остановлен")
    await cache_manager.close()


if __name__ == "__main__":
    import time

    import uvicorn

    print("🌟 Запуск QakeAPI Enhanced Demo...")
    print("✨ Включены все возможности фреймворка!")

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True, log_level="info")
