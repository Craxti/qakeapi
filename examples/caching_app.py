# -*- coding: utf-8 -*-
"""
Пример использования кэширования в QakeAPI.
"""
from __future__ import annotations
import asyncio
from typing import Dict, List, Optional
from qakeapi import Application
from qakeapi.cache import Cache
from qakeapi.core.logging import setup_logging
import time
import random

# Настройка логирования
logger = setup_logging(level="DEBUG")

# Инициализация приложения и кэша
app = Application()
cache_instance = Cache(backend="memory")

# Имитация тяжелых вычислений
def expensive_computation(number: int) -> float:
    """Имитация сложных вычислений."""
    time.sleep(2)  # Имитация долгой работы
    return number * random.random()

@app.get("/compute/{number}")
async def compute(request):
    """Эндпоинт с кэшированием результатов."""
    number = int(request.path_params['number'])
    
    # Пробуем получить из кэша
    cache_key = f"compute:{number}"
    cached_result = await cache_instance.get(cache_key)
    if cached_result is not None:
        return {
            "number": number,
            "result": cached_result,
            "cached": True
        }
    
    # Выполняем вычисления
    result = expensive_computation(number)
    await cache_instance.set(cache_key, result, ttl=30)
    
    return {
        "number": number,
        "result": result,
        "cached": False
    }

@app.get("/compute-nocache/{number}")
async def compute_nocache(request):
    """Тот же эндпоинт, но без кэширования."""
    number = int(request.path_params['number'])
    result = expensive_computation(number)
    return {
        "number": number,
        "result": result,
        "cached": False
    }

@app.delete("/cache/{key}")
async def clear_cache(request):
    """Очистка кэша для конкретного ключа."""
    key = request.path_params['key']
    await cache_instance.delete(f"compute:{key}")
    return {"message": f"Cache cleared for key {key}"}

@app.delete("/cache")
async def clear_all_cache(request):
    """Очистка всего кэша."""
    await cache_instance.clear()
    return {"message": "All cache cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001) 