# -*- coding: utf-8 -*-
"""
Пример использования профилирования в QakeAPI.
"""
import asyncio
from qakeapi import Application
from qakeapi.core.optimization import RequestProfiler
from qakeapi.core.logging import setup_logging
import time

# Настройка логирования и профилирования
logger = setup_logging(level="DEBUG")
profiler = RequestProfiler()

# Инициализация приложения
app = Application()

@app.get("/fast")
@profiler.profile_endpoint
async def fast_endpoint(request):
    """Быстрый эндпоинт."""
    return {"message": "Fast response"}

@app.get("/slow")
@profiler.profile_endpoint
async def slow_endpoint(request):
    """Медленный эндпоинт."""
    time.sleep(2)  # Имитация медленной операции
    return {"message": "Slow response"}

@app.get("/cpu-intensive")
@profiler.profile_endpoint
async def cpu_intensive(request):
    """Эндпоинт с интенсивными вычислениями."""
    result = 0
    for i in range(1000000):
        result += i
    return {"result": result}

@app.get("/memory-intensive")
@profiler.profile_endpoint
async def memory_intensive(request):
    """Эндпоинт с интенсивным использованием памяти."""
    big_list = list(range(1000000))  # Создаем большой список
    return {"length": len(big_list)}

@app.get("/stats")
async def get_stats(request):
    """Получение статистики профилирования."""
    return profiler.get_stats()

@app.get("/stats/{endpoint_id}")
async def get_endpoint_stats(request):
    """Получение статистики конкретного запроса."""
    endpoint_id = request.path_params['endpoint_id']
    return profiler.get_stats(endpoint_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002) 