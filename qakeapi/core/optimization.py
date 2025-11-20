"""
Performance optimization utilities for QakeAPI.
"""
from typing import Optional, Dict, Any, List
import time
import asyncio
from contextlib import contextmanager
import logging
from functools import wraps
import statistics
import psutil

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Generic connection pool implementation."""
    
    def __init__(
        self,
        min_size: int = 5,
        max_size: int = 20,
        timeout: float = 30.0
    ):
        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        self._pool: List[Any] = []
        self._in_use: Dict[Any, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self) -> Any:
        """Acquire a connection from the pool."""
        async with self._lock:
            # Try to get an available connection
            while self._pool:
                conn = self._pool.pop()
                if await self._is_connection_valid(conn):
                    self._in_use[conn] = time.time()
                    return conn
            
            # Create new connection if below max_size
            if len(self._in_use) < self._max_size:
                conn = await self._create_connection()
                self._in_use[conn] = time.time()
                return conn
            
            # Wait for a connection to become available
            while True:
                # Check for timed out connections
                current_time = time.time()
                for conn, start_time in list(self._in_use.items()):
                    if current_time - start_time > self._timeout:
                        await self._close_connection(conn)
                        del self._in_use[conn]
                
                if len(self._in_use) < self._max_size:
                    conn = await self._create_connection()
                    self._in_use[conn] = time.time()
                    return conn
                
                await asyncio.sleep(0.1)

    async def release(self, conn: Any) -> None:
        """Release a connection back to the pool."""
        async with self._lock:
            if conn in self._in_use:
                del self._in_use[conn]
                if len(self._pool) < self._min_size:
                    self._pool.append(conn)
                else:
                    await self._close_connection(conn)

    async def _create_connection(self) -> Any:
        """Create a new connection. Override in subclass."""
        raise NotImplementedError

    async def _close_connection(self, conn: Any) -> None:
        """Close a connection. Override in subclass."""
        raise NotImplementedError

    async def _is_connection_valid(self, conn: Any) -> bool:
        """Check if connection is valid. Override in subclass."""
        return True

class RequestProfiler:
    """Профилировщик запросов."""
    
    def __init__(self):
        """Инициализация профилировщика."""
        self.stats: Dict[str, List[float]] = {}
        self.detailed_stats: Dict[str, List[Dict]] = {}
    
    def profile_endpoint(self, func):
        """Декоратор для профилирования эндпоинта."""
        endpoint_name = func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise e
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                duration = (end_time - start_time) * 1000  # в миллисекундах
                memory_used = end_memory - start_memory
                
                # Сохраняем статистику
                if endpoint_name not in self.stats:
                    self.stats[endpoint_name] = []
                self.stats[endpoint_name].append(duration)
                
                if endpoint_name not in self.detailed_stats:
                    self.detailed_stats[endpoint_name] = []
                self.detailed_stats[endpoint_name].append({
                    'timestamp': time.time(),
                    'duration_ms': duration,
                    'memory_bytes': memory_used,
                    'success': success
                })
                
                # Логируем информацию о запросе
                logger.info(
                    f"Request profiling: {endpoint_name}",
                    extra={
                        'endpoint': endpoint_name,
                        'duration_ms': duration,
                        'memory_bytes': memory_used,
                        'success': success
                    }
                )
            
            return result
        return wrapper
    
    def get_stats(self, endpoint_name: Optional[str] = None) -> Dict:
        """
        Получение статистики профилирования.
        
        Args:
            endpoint_name: Имя эндпоинта (если None, возвращает статистику по всем эндпоинтам)
        """
        if endpoint_name:
            if endpoint_name not in self.stats:
                return {}
                
            durations = self.stats[endpoint_name]
            detailed = self.detailed_stats[endpoint_name]
            
            return {
                'count': len(durations),
                'avg_duration_ms': statistics.mean(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'median_duration_ms': statistics.median(durations),
                'success_rate': sum(1 for d in detailed if d['success']) / len(detailed),
                'total_memory_bytes': sum(d['memory_bytes'] for d in detailed)
            }
        
        # Статистика по всем эндпоинтам
        return {
            name: self.get_stats(name)
            for name in self.stats.keys()
        }
    
    def reset_stats(self, endpoint_name: Optional[str] = None) -> None:
        """
        Сброс статистики профилирования.
        
        Args:
            endpoint_name: Имя эндпоинта (если None, сбрасывает статистику по всем эндпоинтам)
        """
        if endpoint_name:
            if endpoint_name in self.stats:
                self.stats[endpoint_name] = []
                self.detailed_stats[endpoint_name] = []
        else:
            self.stats.clear()
            self.detailed_stats.clear()

def profile_endpoint(profiler: RequestProfiler):
    """Decorator for profiling endpoint execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = str(time.time())
            with profiler.profile(request_id):
                return await func(*args, **kwargs)
        return wrapper
    return decorator 