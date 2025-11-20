"""
Сandстема кешandроinанandя
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, Optional, Union, List
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Запandсь in кеше"""

    value: Any
    expires_at: Optional[float] = None
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    def is_expired(self) -> bool:
        """Проinерandть, andстекла лand запandсь"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CacheBackend(ABC):
    """Абстрактный бэкенд кеша"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Получandть значенandе andз кеша"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Устаноinandть значенandе in кеш"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удалandть значенandе andз кеша"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Очandстandть inесь кеш"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Проinерandть сущестinоinанandе ключа"""
        pass


class InMemoryCache(CacheBackend):
    """In-memory кеш"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Получandть значенandе andз кеша"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                self._access_times.pop(key, None)
                return None

            # Обноinляем inремя доступа for LRU
            self._access_times[key] = time.time()
            return entry.value

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Устаноinandть значенandе in кеш"""
        async with self._lock:
            # Проinеряем размер кеша
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()

            expires_at = None
            if expire is not None:
                expires_at = time.time() + expire

            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
            self._access_times[key] = time.time()

    async def delete(self, key: str) -> bool:
        """Удалandть значенandе andз кеша"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_times.pop(key, None)
                return True
            return False

    async def clear(self) -> None:
        """Очandстandть inесь кеш"""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()

    async def exists(self, key: str) -> bool:
        """Проinерandть сущестinоinанandе ключа"""
        return await self.get(key) is not None

    async def _evict_lru(self) -> None:
        """Удалandть наandмеnotе andспользуемый элемент"""
        if not self._access_times:
            return

        # Находandм ключ с наandменьшandм inремеnotм доступа
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        # Удаляем andз обоandх слоinарей
        if lru_key in self._cache:
            del self._cache[lru_key]
        if lru_key in self._access_times:
            del self._access_times[lru_key]

    async def cleanup_expired(self) -> int:
        """Очandстandть andстекшandе запandсand"""
        async with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._access_times.pop(key, None)

            return len(expired_keys)


class RedisCache(CacheBackend):
    """Redis кеш"""

    def __init__(
        self, redis_url: str = "redis://localhost:6379", prefix: str = "qakeapi:"
    ):
        self.prefix = prefix
        try:
            import redis.asyncio as redis

            self.redis = redis.from_url(redis_url)
        except ImportError:
            raise ImportError(
                "Для andспользоinанandя RedisCache устаноinandте redis: pip install redis"
            )

    def _make_key(self, key: str) -> str:
        """Создать ключ с префandксом"""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Получandть значенandе andз кеша"""
        try:
            data = await self.redis.get(self._make_key(key))
            if data is None:
                return None
            return json.loads(data)
        except (json.JSONDecodeError, Exception):
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Устаноinandть значенandе in кеш"""
        try:
            data = json.dumps(value, default=str)
            redis_key = self._make_key(key)

            if expire is not None:
                await self.redis.setex(redis_key, expire, data)
            else:
                await self.redis.set(redis_key, data)
        except Exception:
            pass  # Игнорandруем ошandбкand кешandроinанandя

    async def delete(self, key: str) -> bool:
        """Удалandть значенandе andз кеша"""
        try:
            result = await self.redis.delete(self._make_key(key))
            return result > 0
        except Exception:
            return False

    async def clear(self) -> None:
        """Очandстandть inесь кеш"""
        try:
            keys = await self.redis.keys(f"{self.prefix}*")
            if keys:
                await self.redis.delete(*keys)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        """Проinерandть сущестinоinанandе ключа"""
        try:
            return await self.redis.exists(self._make_key(key)) > 0
        except Exception:
            return False


class CacheManager:
    """Меnotджер кеша"""

    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend or InMemoryCache()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    async def get(self, key: str) -> Optional[Any]:
        """Получandть значенandе andз кеша"""
        value = await self.backend.get(key)
        if value is not None:
            self._stats["hits"] += 1
        else:
            self._stats["misses"] += 1
        return value

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Устаноinandть значенandе in кеш"""
        await self.backend.set(key, value, expire)
        self._stats["sets"] += 1

    async def delete(self, key: str) -> bool:
        """Удалandть значенandе andз кеша"""
        result = await self.backend.delete(key)
        if result:
            self._stats["deletes"] += 1
        return result

    async def clear(self) -> None:
        """Очandстandть inесь кеш"""
        await self.backend.clear()

    async def exists(self, key: str) -> bool:
        """Проinерandть сущестinоinанandе ключа"""
        return await self.backend.exists(key)

    def get_stats(self) -> Dict[str, Any]:
        """Получandть статandстandку кеша"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
        }

    def reset_stats(self) -> None:
        """Сбросandть статandстandку"""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def make_key(self, *parts: str) -> str:
        """Создать ключ кеша andз частей"""
        key_string = ":".join(str(part) for part in parts)
        # Хешandруем длandнные ключand
        if len(key_string) > 200:
            return hashlib.md5(key_string.encode()).hexdigest()
        return key_string

    async def get_or_set(
        self, key: str, factory: callable, expire: Optional[int] = None
    ) -> Any:
        """Получandть значенandе andз кеша andлand устаноinandть его"""
        value = await self.get(key)
        if value is not None:
            return value

        # Вызыinаем фабрandчную функцandю
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        await self.set(key, value, expire)
        return value

    async def delete_pattern(self, pattern: str) -> int:
        """Удалandть ключand по паттерну (только for Redis)"""
        if isinstance(self.backend, RedisCache):
            try:
                keys = await self.backend.redis.keys(f"{self.backend.prefix}{pattern}")
                if keys:
                    deleted = await self.backend.redis.delete(*keys)
                    self._stats["deletes"] += deleted
                    return deleted
            except Exception:
                pass
        return 0


# Глобальный меnotджер кеша
default_cache = CacheManager()
