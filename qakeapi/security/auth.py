"""
Модуль аутентификации и авторизации для QakeAPI.
"""
from functools import wraps
from typing import List, Optional
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Настройки безопасности
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"  # В продакшене использовать безопасный ключ
ALGORITHM = "HS256"

class SecurityUtils:
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хеширование пароля."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        """Декодирование JWT токена."""
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def require_auth(scopes: List[str] = None):
    """Декоратор для защиты эндпоинтов."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # В реальном приложении здесь должна быть проверка токена
            # и прав доступа
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(limit: int = 100, window: int = 60):
    """Декоратор для ограничения частоты запросов."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # В реальном приложении здесь должна быть проверка
            # количества запросов
            return await func(*args, **kwargs)
        return wrapper
    return decorator 