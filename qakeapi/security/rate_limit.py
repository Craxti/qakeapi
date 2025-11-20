from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import time
import asyncio
from dataclasses import dataclass
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response


@dataclass
class RateLimitInfo:
    """Информация о текущих ограничениях запросов"""
    remaining: int  # Оставшееся количество запросов
    reset: float   # Время сброса в секундах
    limit: int     # Максимальное количество запросов


class RateLimiter(ABC):
    """Абстрактный базовый класс для rate limiting"""
    
    @abstractmethod
    async def is_allowed(self, key: str) -> Tuple[bool, RateLimitInfo]:
        """Проверяет, разрешен ли запрос"""
        pass

    @abstractmethod
    async def update(self, key: str):
        """Обновляет состояние после запроса"""
        pass


class InMemoryRateLimiter(RateLimiter):
    """Реализация rate limiting в памяти"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window = 60  # окно в секундах
        self.storage: Dict[str, Dict[float, int]] = {}
        
    async def is_allowed(self, key: str) -> Tuple[bool, RateLimitInfo]:
        now = time.time()
        if key not in self.storage:
            self.storage[key] = {}
            
        # Очистка устаревших записей
        self.storage[key] = {
            ts: count for ts, count in self.storage[key].items()
            if now - ts < self.window
        }
        
        # Подсчет текущих запросов
        current_requests = sum(self.storage[key].values())
        
        # Вычисление оставшегося времени до сброса
        if self.storage[key]:
            oldest_ts = min(self.storage[key].keys())
            reset_time = oldest_ts + self.window
        else:
            reset_time = now + self.window
            
        info = RateLimitInfo(
            remaining=max(0, self.requests_per_minute - current_requests - 1),  # Учитываем текущий запрос
            reset=reset_time,
            limit=self.requests_per_minute
        )
        
        return current_requests < self.requests_per_minute, info
    
    async def update(self, key: str):
        now = time.time()
        if key not in self.storage:
            self.storage[key] = {}
        self.storage[key][now] = self.storage[key].get(now, 0) + 1


class RateLimitMiddleware:
    """Middleware для rate limiting"""
    
    def __init__(
        self,
        rate_limiter: RateLimiter,
        key_func=lambda request: request.client[0]  # Используем IP адрес из кортежа client
    ):
        self.rate_limiter = rate_limiter
        self.key_func = key_func
        
    async def __call__(
        self,
        request: Request,
        handler
    ) -> Response:
        key = self.key_func(request)
        allowed, info = await self.rate_limiter.is_allowed(key)
        
        # Добавляем заголовки rate limiting
        rate_limit_headers = {
            "X-RateLimit-Limit": str(info.limit),
            "X-RateLimit-Remaining": str(info.remaining),
            "X-RateLimit-Reset": str(int(info.reset))
        }
        
        if not allowed:
            return Response.json(
                {"error": "Rate limit exceeded"},
                status_code=429,
                headers=rate_limit_headers
            )
            
        await self.rate_limiter.update(key)
        response = await handler(request)
        
        # Добавляем заголовки к ответу
        for name, value in rate_limit_headers.items():
            response.headers.append((name.encode(), value.encode()))
            
        return response 