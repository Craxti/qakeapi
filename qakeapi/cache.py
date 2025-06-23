# -*- coding: utf-8 -*-
"""
Модуль кэширования для QakeAPI.
"""
from typing import Any, Optional, Union
from functools import wraps
import json
import time
import os
from pathlib import Path

class Cache:
    """Базовый класс для кэширования."""
    
    def __init__(self, backend: str = "memory", **kwargs):
        """
        Инициализация кэша.
        
        Args:
            backend: Тип бэкенда ('memory' или 'file')
            **kwargs: Дополнительные параметры
        """
        self.backend = backend
        if backend == "memory":
            self._cache = {}
        elif backend == "file":
            self.cache_dir = kwargs.get('cache_dir', '.cache')
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        else:
            raise ValueError(f"Unsupported cache backend: {backend}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша."""
        if self.backend == "memory":
            return self._get_memory(key)
        else:
            return self._get_file(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установка значения в кэш."""
        if self.backend == "memory":
            self._set_memory(key, value, ttl)
        else:
            self._set_file(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """Удаление значения из кэша."""
        if self.backend == "memory":
            self._delete_memory(key)
        else:
            self._delete_file(key)
    
    async def clear(self) -> None:
        """Очистка всего кэша."""
        if self.backend == "memory":
            self._cache.clear()
        else:
            for file in Path(self.cache_dir).glob("*.cache"):
                file.unlink()
    
    def _get_memory(self, key: str) -> Optional[Any]:
        """Получение значения из памяти."""
        if key not in self._cache:
            return None
            
        value, expire_at = self._cache[key]
        if expire_at and time.time() > expire_at:
            del self._cache[key]
            return None
            
        return value
    
    def _set_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установка значения в память."""
        expire_at = time.time() + ttl if ttl else None
        self._cache[key] = (value, expire_at)
    
    def _delete_memory(self, key: str) -> None:
        """Удаление значения из памяти."""
        self._cache.pop(key, None)
    
    def _get_file(self, key: str) -> Optional[Any]:
        """Получение значения из файла."""
        file_path = Path(self.cache_dir) / f"{key}.cache"
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if data['expire_at'] and time.time() > data['expire_at']:
                file_path.unlink()
                return None
                
            return data['value']
        except (json.JSONDecodeError, KeyError):
            return None
    
    def _set_file(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Установка значения в файл."""
        file_path = Path(self.cache_dir) / f"{key}.cache"
        expire_at = time.time() + ttl if ttl else None
        
        data = {
            'value': value,
            'expire_at': expire_at
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f)
    
    def _delete_file(self, key: str) -> None:
        """Удаление значения из файла."""
        file_path = Path(self.cache_dir) / f"{key}.cache"
        if file_path.exists():
            file_path.unlink()

def cache(ttl: Optional[int] = None):
    """
    Декоратор для кэширования результатов функции.
    
    Args:
        ttl: Время жизни кэша в секундах
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерация ключа кэша
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Получение значения из кэша
            cached_value = await wrapper.cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Выполнение функции и кэширование результата
            result = await func(*args, **kwargs)
            await wrapper.cache.set(cache_key, result, ttl)
            return result
        
        # Создание экземпляра кэша для функции
        wrapper.cache = Cache()
        return wrapper
    return decorator 