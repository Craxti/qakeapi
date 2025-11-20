"""
Улучшенный пример QakeAPI со всеми новыми возможностями
"""
import os
from typing import List, Optional
from pydantic import BaseModel, Field

from qakeapi import (
    QakeAPI,
    Request,
    JSONResponse,
    Depends,
    # Security
    JWTManager,
    PasswordManager,
    SecurityConfig,
    SecurityValidator,
    RateLimitMiddleware,
    RateLimitRule,
    # Middleware
    CompressionMiddleware,
    CacheMiddleware,
    CORSMiddleware,
    # Caching
    CacheManager,
    InMemoryCache,
    # Error handling
    ErrorHandler,
    # Config
    Settings,
    # Utils
    status,
)
from qakeapi.core.exceptions import HTTPException


# Конфигурация
settings = Settings(
    app_name="Enhanced QakeAPI Demo",
    app_version="2.0.0",
    debug=True,
    secret_key=os.getenv("SECRET_KEY", "demo-secret-key-change-in-production"),
)

# Настройка безопасности
security_config = SecurityConfig(
    secret_key=settings.secret_key,
    access_token_expire_minutes=30,
    password_min_length=8,
)

# Менеджеры
jwt_manager = JWTManager(security_config)
password_manager = PasswordManager(security_config)
cache_manager = CacheManager(InMemoryCache(max_size=1000))
security_validator = SecurityValidator()
error_handler = ErrorHandler(debug=settings.debug)

# Создаем приложение
app = QakeAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Демонстрация всех возможностей улучшенного QakeAPI",
    debug=settings.debug,
)

# Добавляем middleware (порядок важен!)
app.add_middleware(CompressionMiddleware(minimum_size=500, compression_level=6))

app.add_middleware(
    CacheMiddleware(
        cache_manager=cache_manager,
        default_expire=300,  # 5 минут
        skip_paths={"/auth/login", "/auth/register", "/admin/*"},
    )
)

app.add_middleware(
    CORSMiddleware(
        allow_origins=["http://localhost:3000", "https://myapp.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        allow_credentials=True,
    )
)

# Rate limiting с разными правилами для разных путей
rate_limiter = RateLimitMiddleware()
rate_limiter.rate_limiter.add_rule(
    "/auth/*",
    RateLimitRule(requests=5, window=60, message="Слишком много попыток входа"),
)
rate_limiter.rate_limiter.add_rule(
    "/api/upload",
    RateLimitRule(requests=3, window=60, message="Лимит загрузок превышен"),
)
app.add_middleware(rate_limiter)

# Настраиваем обработку ошибок
app.exception_handlers[Exception] = error_handler.handle_exception


# Модели данных
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    tags: List[str] = Field(default_factory=list)


class Post(BaseModel):
    id: int
    title: str
    content: str
    tags: List[str]
    author_id: int
    created_at: str


# Фиктивная база данных
fake_users_db = {}
fake_posts_db = {}
user_counter = 0
post_counter = 0


# Зависимости
async def get_current_user(request: Request) -> User:
    """Получить текущего пользователя из JWT токена"""
    auth_header = request.get_header("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status.UNAUTHORIZED, "Токен не предоставлен")

    token = auth_header.split(" ")[1]
    try:
        token_data = jwt_manager.verify_token(token, "access")
        user_id = token_data.user_id

        if user_id not in fake_users_db:
            raise HTTPException(status.UNAUTHORIZED, "Пользователь не найден")

        return fake_users_db[user_id]
    except Exception as e:
        raise HTTPException(status.UNAUTHORIZED, f"Невалидный токен: {str(e)}")


# Маршруты


@app.get("/")
async def root():
    """Главная страница с информацией о возможностях"""
    return {
        "message": f"Добро пожаловать в {settings.app_name}!",
        "version": settings.app_version,
        "features": [
            "🔐 JWT аутентификация с безопасным хешированием паролей",
            "🚦 Rate limiting с гибкими правилами",
            "🗜️ Автоматическое сжатие ответов (gzip)",
            "💾 Интеллектуальное кеширование",
            "🛡️ Валидация и санитизация входных данных",
            "📊 Улучшенная обработка ошибок с логированием",
            "⚙️ Централизованное управление конфигурацией",
            "🔧 CORS с настраиваемыми правилами",
        ],
        "endpoints": {
            "auth": "/auth/register, /auth/login, /auth/refresh",
            "users": "/users/me, /users",
            "posts": "/posts, /posts/{id}",
            "admin": "/admin/stats, /admin/cache",
            "docs": "/docs, /redoc",
        },
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "cache_stats": cache_manager.get_stats(),
        "users_count": len(fake_users_db),
        "posts_count": len(fake_posts_db),
    }


# Аутентификация
@app.post("/auth/register")
async def register(user_data: UserCreate):
    """Регистрация нового пользователя"""
    global user_counter

    # Валидируем входные данные
    clean_data = security_validator.validate_data(user_data.dict())

    # Проверяем уникальность
    for user in fake_users_db.values():
        if user.username == clean_data["username"]:
            raise HTTPException(status.BAD_REQUEST, "Пользователь уже существует")
        if user.email == clean_data["email"]:
            raise HTTPException(status.BAD_REQUEST, "Email уже используется")

    # Хешируем пароль
    hashed_password = password_manager.hash_password(clean_data["password"])

    # Создаем пользователя
    user_counter += 1
    user = User(
        id=user_counter,
        username=clean_data["username"],
        email=clean_data["email"],
        full_name=clean_data.get("full_name"),
    )

    fake_users_db[user_counter] = user
    # Сохраняем хешированный пароль отдельно (в реальном приложении - в БД)
    fake_users_db[f"{user_counter}_password"] = hashed_password

    # Создаем токены
    token_pair = jwt_manager.create_token_pair(
        {"user_id": user.id, "username": user.username, "email": user.email}
    )

    return {
        "message": "Пользователь успешно зарегистрирован",
        "user": user.dict(),
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": token_pair.token_type,
        "expires_in": token_pair.expires_in,
    }


@app.post("/auth/login")
async def login(credentials: UserLogin):
    """Вход в систему"""
    # Валидируем входные данные
    clean_data = security_validator.validate_data(credentials.dict())

    # Ищем пользователя
    user = None
    for u in fake_users_db.values():
        if isinstance(u, User) and u.username == clean_data["username"]:
            user = u
            break

    if not user:
        raise HTTPException(status.UNAUTHORIZED, "Неверные учетные данные")

    # Проверяем пароль
    stored_password = fake_users_db.get(f"{user.id}_password")
    if not stored_password or not password_manager.verify_password(
        clean_data["password"], stored_password
    ):
        raise HTTPException(status.UNAUTHORIZED, "Неверные учетные данные")

    # Создаем токены
    token_pair = jwt_manager.create_token_pair(
        {"user_id": user.id, "username": user.username, "email": user.email}
    )

    return {
        "message": "Успешный вход",
        "user": user.dict(),
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": token_pair.token_type,
        "expires_in": token_pair.expires_in,
    }


@app.post("/auth/refresh")
async def refresh_token(request: Request):
    """Обновление access токена"""
    data = await request.json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status.BAD_REQUEST, "Refresh token не предоставлен")

    try:
        new_access_token = jwt_manager.refresh_access_token(refresh_token)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": security_config.access_token_expire_minutes * 60,
        }
    except Exception as e:
        raise HTTPException(status.UNAUTHORIZED, f"Невалидный refresh token: {str(e)}")


# Пользователи
@app.get("/users/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {"user": current_user.dict(), "message": "Информация о текущем пользователе"}


@app.get("/users")
async def get_users(
    skip: int = 0, limit: int = 10, current_user: User = Depends(get_current_user)
):
    """Получить список пользователей (кешируется)"""

    # Используем кеширование для этого запроса
    cache_key = f"users_list_{skip}_{limit}"

    async def get_users_data():
        users = [u for u in fake_users_db.values() if isinstance(u, User)]
        return {
            "users": [u.dict() for u in users[skip : skip + limit]],
            "total": len(users),
            "skip": skip,
            "limit": limit,
        }

    return await cache_manager.get_or_set(cache_key, get_users_data, expire=60)


# Посты
@app.get("/posts")
async def get_posts(skip: int = 0, limit: int = 10, tag: Optional[str] = None):
    """Получить список постов (кешируется и сжимается)"""

    cache_key = f"posts_list_{skip}_{limit}_{tag or 'all'}"

    async def get_posts_data():
        posts = list(fake_posts_db.values())

        # Фильтрация по тегу
        if tag:
            posts = [p for p in posts if tag in p.tags]

        return {
            "posts": posts[skip : skip + limit],
            "total": len(posts),
            "skip": skip,
            "limit": limit,
            "filter": {"tag": tag} if tag else None,
        }

    return await cache_manager.get_or_set(cache_key, get_posts_data, expire=120)


@app.post("/posts")
async def create_post(
    post_data: PostCreate, current_user: User = Depends(get_current_user)
):
    """Создать новый пост"""
    global post_counter

    # Валидируем входные данные
    clean_data = security_validator.validate_data(post_data.dict())

    # Создаем пост
    post_counter += 1
    post = Post(
        id=post_counter,
        title=clean_data["title"],
        content=clean_data["content"],
        tags=clean_data.get("tags", []),
        author_id=current_user.id,
        created_at="2024-01-01T00:00:00Z",  # В реальном приложении - текущее время
    )

    fake_posts_db[post_counter] = post

    # Очищаем кеш постов
    await cache_manager.delete_pattern("posts_list_*")

    return {"message": "Пост успешно создан", "post": post.dict()}


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    """Получить пост по ID (кешируется)"""

    cache_key = f"post_{post_id}"

    async def get_post_data():
        if post_id not in fake_posts_db:
            raise HTTPException(status.NOT_FOUND, "Пост не найден")

        post = fake_posts_db[post_id]
        author = fake_users_db.get(post.author_id)

        return {"post": post.dict(), "author": author.dict() if author else None}

    return await cache_manager.get_or_set(cache_key, get_post_data, expire=300)


# Административные маршруты
@app.get("/admin/stats")
async def admin_stats(current_user: User = Depends(get_current_user)):
    """Статистика системы (только для авторизованных)"""
    return {
        "system_stats": {
            "users_total": len(
                [u for u in fake_users_db.values() if isinstance(u, User)]
            ),
            "posts_total": len(fake_posts_db),
            "cache_stats": cache_manager.get_stats(),
        },
        "app_info": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
        },
    }


@app.post("/admin/cache/clear")
async def clear_cache(current_user: User = Depends(get_current_user)):
    """Очистить кеш (только для авторизованных)"""
    await cache_manager.clear()
    cache_manager.reset_stats()

    return {"message": "Кеш успешно очищен", "timestamp": "2024-01-01T00:00:00Z"}


# Тестовые маршруты для демонстрации возможностей
@app.get("/demo/large-response")
async def large_response():
    """Большой ответ для демонстрации сжатия"""
    return {
        "message": "Этот ответ содержит много данных для демонстрации сжатия",
        "data": [
            {
                "id": i,
                "title": f"Элемент номер {i}",
                "description": f"Подробное описание элемента {i} " * 10,
                "metadata": {
                    "created": "2024-01-01",
                    "updated": "2024-01-01",
                    "tags": [f"tag{j}" for j in range(5)],
                },
            }
            for i in range(100)
        ],
    }


@app.post("/demo/validation")
async def validation_demo(request: Request):
    """Демонстрация валидации и санитизации"""
    data = await request.json()

    # Применяем валидацию
    clean_data = security_validator.validate_data(data)

    return {
        "message": "Данные успешно валидированы и санитизированы",
        "original_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
        "cleaned_data": clean_data,
        "validation_applied": True,
    }


@app.get("/demo/error")
async def error_demo():
    """Демонстрация обработки ошибок"""
    raise ValueError("Это демонстрационная ошибка для показа улучшенной обработки")


# События жизненного цикла
@app.on_event("startup")
async def startup():
    """Инициализация при запуске"""
    print(f"Запуск {settings.app_name} v{settings.app_version}...")
    print(f"Debug режим: {'включен' if settings.debug else 'выключен'}")
    print(f"Кеш: {type(cache_manager.backend).__name__}")
    print(f"JWT: настроен с {security_config.algorithm}")

    # Создаем тестового пользователя
    global user_counter
    user_counter += 1
    test_user = User(
        id=user_counter,
        username="demo",
        email="demo@example.com",
        full_name="Demo User",
    )
    fake_users_db[user_counter] = test_user
    fake_users_db[f"{user_counter}_password"] = password_manager.hash_password(
        "DemoPassword123!"
    )

    print(f"Создан тестовый пользователь: demo / DemoPassword123!")


@app.on_event("shutdown")
async def shutdown():
    """Очистка при завершении"""
    print(f"{settings.app_name} завершает работу...")
    await cache_manager.clear()
    print("Кеш очищен")


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print(f"Запуск {settings.app_name} v{settings.app_version}")
    print("=" * 60)
    print("Документация: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("Тестовый пользователь: demo / DemoPassword123!")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
