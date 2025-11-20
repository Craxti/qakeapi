"""
Продвинутый пример использования QakeAPI с аутентификацией, валидацией и WebSocket
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from qakeapi import QakeAPI, Request, JSONResponse, Depends, WebSocket
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware
from qakeapi.middleware.auth import BearerTokenMiddleware, APIKeyMiddleware
from qakeapi.core.exceptions import HTTPException
from qakeapi.utils.status import status


# Модели данных
class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)


class Item(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    owner_id: int


class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)


# Создаем приложение
app = QakeAPI(
    title="Продвинутое QakeAPI приложение",
    description="Пример приложения с аутентификацией, валидацией и WebSocket",
    version="2.0.0",
    debug=True,
)

# Добавляем middleware
app.add_middleware(
    CORSMiddleware(
        allow_origins=["http://localhost:3000", "https://myapp.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        allow_credentials=True,
    )
)
app.add_middleware(LoggingMiddleware())

# Аутентификация
SECRET_KEY = "your-secret-key-here"
API_KEYS = {
    "test-api-key": {"name": "Test Client", "permissions": ["read", "write"]},
    "readonly-key": {"name": "Read Only Client", "permissions": ["read"]},
}

app.add_middleware(
    BearerTokenMiddleware(
        secret_key=SECRET_KEY,
        skip_paths={
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/public/*",
        },
    )
)

# Фиктивная база данных
fake_users_db = {
    1: User(id=1, name="Алиса", email="alice@example.com"),
    2: User(id=2, name="Боб", email="bob@example.com"),
}

fake_items_db = {
    1: Item(
        id=1, title="Ноутбук", description="Мощный ноутбук", price=50000.0, owner_id=1
    ),
    2: Item(
        id=2, title="Мышь", description="Беспроводная мышь", price=1500.0, owner_id=1
    ),
    3: Item(
        id=3,
        title="Клавиатура",
        description="Механическая клавиатура",
        price=5000.0,
        owner_id=2,
    ),
}


# Зависимости
async def get_current_user(request: Request) -> User:
    """Получить текущего пользователя из токена"""
    user_info = getattr(request, "_user", None)
    if not user_info:
        raise HTTPException(status.UNAUTHORIZED, "Not authenticated")

    user_id = user_info.get("user_id")
    if not user_id or user_id not in fake_users_db:
        raise HTTPException(status.UNAUTHORIZED, "User not found")

    return fake_users_db[user_id]


def get_api_key_info(request: Request) -> dict:
    """Получить информацию об API ключе"""
    api_key = request.get_header("x-api-key")
    if not api_key or api_key not in API_KEYS:
        raise HTTPException(status.UNAUTHORIZED, "Invalid API key")

    return API_KEYS[api_key]


# Публичные маршруты
@app.get("/")
async def root():
    """Главная страница"""
    return {
        "message": "Добро пожаловать в продвинутое QakeAPI приложение!",
        "features": [
            "Аутентификация JWT",
            "Валидация данных с Pydantic",
            "WebSocket поддержка",
            "Middleware система",
            "Автоматическая документация API",
        ],
    }


@app.get("/public/info")
async def public_info():
    """Публичная информация"""
    return {
        "app_name": "QakeAPI Advanced App",
        "version": "2.0.0",
        "endpoints": len(app.routes),
    }


# Аутентификация
@app.post("/auth/login")
async def login(request: Request):
    """Вход в систему"""
    import json
    import base64
    import hmac
    import hashlib
    import time

    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    # Простая проверка (в реальном приложении используйте хеширование паролей)
    user = None
    for u in fake_users_db.values():
        if u.email == email:
            user = u
            break

    if not user or password != "password123":  # Простая проверка
        raise HTTPException(status.UNAUTHORIZED, "Invalid credentials")

    # Создаем JWT токен
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": int(time.time()) + 3600,  # 1 час
    }

    header_b64 = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )

    message = f"{header_b64}.{payload_b64}"
    signature = (
        base64.urlsafe_b64encode(
            hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
        )
        .decode()
        .rstrip("=")
    )

    token = f"{message}.{signature}"

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.dict(),
    }


# Защищенные маршруты для пользователей
@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user


@app.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    """Получить список всех пользователей"""
    return list(fake_users_db.values())


@app.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate, current_user: User = Depends(get_current_user)
):
    """Создать нового пользователя"""
    new_id = max(fake_users_db.keys()) + 1
    new_user = User(
        id=new_id,
        name=user_data.name,
        email=user_data.email,
    )
    fake_users_db[new_id] = new_user
    return new_user


# Маршруты для работы с элементами
@app.get("/items", response_model=List[Item])
async def get_items(
    skip: int = 0, limit: int = 10, current_user: User = Depends(get_current_user)
):
    """Получить список элементов"""
    items = list(fake_items_db.values())
    return items[skip : skip + limit]


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int, current_user: User = Depends(get_current_user)):
    """Получить элемент по ID"""
    if item_id not in fake_items_db:
        raise HTTPException(status.NOT_FOUND, "Item not found")
    return fake_items_db[item_id]


@app.post("/items", response_model=Item)
async def create_item(
    item_data: ItemCreate, current_user: User = Depends(get_current_user)
):
    """Создать новый элемент"""
    new_id = max(fake_items_db.keys()) + 1
    new_item = Item(
        id=new_id,
        title=item_data.title,
        description=item_data.description,
        price=item_data.price,
        owner_id=current_user.id,
    )
    fake_items_db[new_id] = new_item
    return new_item


@app.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int, item_data: ItemCreate, current_user: User = Depends(get_current_user)
):
    """Обновить элемент"""
    if item_id not in fake_items_db:
        raise HTTPException(status.NOT_FOUND, "Item not found")

    item = fake_items_db[item_id]
    if item.owner_id != current_user.id:
        raise HTTPException(status.FORBIDDEN, "Not enough permissions")

    item.title = item_data.title
    item.description = item_data.description
    item.price = item_data.price

    return item


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, current_user: User = Depends(get_current_user)):
    """Удалить элемент"""
    if item_id not in fake_items_db:
        raise HTTPException(status.NOT_FOUND, "Item not found")

    item = fake_items_db[item_id]
    if item.owner_id != current_user.id:
        raise HTTPException(status.FORBIDDEN, "Not enough permissions")

    del fake_items_db[item_id]
    return {"message": "Item deleted successfully"}


# API ключи маршруты
@app.get("/api/stats")
async def get_api_stats(api_key_info: dict = Depends(get_api_key_info)):
    """Получить статистику API (требует API ключ)"""
    if "read" not in api_key_info.get("permissions", []):
        raise HTTPException(status.FORBIDDEN, "Insufficient permissions")

    return {
        "total_users": len(fake_users_db),
        "total_items": len(fake_items_db),
        "api_client": api_key_info["name"],
    }


# WebSocket
connected_clients = set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket соединение для чата"""
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Подключено к чату!",
                "clients_count": len(connected_clients),
            }
        )

        # Уведомляем других клиентов о новом подключении
        for client in connected_clients:
            if client != websocket:
                try:
                    await client.send_json(
                        {
                            "type": "user_joined",
                            "message": "Новый пользователь присоединился к чату",
                            "clients_count": len(connected_clients),
                        }
                    )
                except:
                    pass

        async for message in websocket.iter_json():
            # Пересылаем сообщение всем подключенным клиентам
            for client in connected_clients.copy():
                try:
                    await client.send_json(
                        {
                            "type": "message",
                            "data": message,
                            "timestamp": int(time.time()),
                        }
                    )
                except:
                    connected_clients.discard(client)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)

        # Уведомляем других клиентов об отключении
        for client in connected_clients.copy():
            try:
                await client.send_json(
                    {
                        "type": "user_left",
                        "message": "Пользователь покинул чат",
                        "clients_count": len(connected_clients),
                    }
                )
            except:
                connected_clients.discard(client)


# Обработчики исключений
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Кастомный обработчик 404 ошибок"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Страница не найдена",
            "message": f"Путь '{request.path}' не существует",
            "suggestion": "Проверьте URL или обратитесь к документации API",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Кастомный обработчик внутренних ошибок"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "message": "Что-то пошло не так. Попробуйте позже.",
            "request_id": id(request),  # В реальном приложении используйте UUID
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
