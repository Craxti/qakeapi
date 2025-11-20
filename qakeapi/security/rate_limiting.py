"""
Сandстема огранandченandя скоростand requestоin (Rate Limiting)
"""
import asyncio
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque

from ..core.request import Request
from ..core.response import Response, JSONResponse
from ..middleware.base import BaseMiddleware
from ..core.exceptions import HTTPException
from ..utils.status import status


@dataclass
class RateLimitRule:
    """Праinandло огранandченandя скоростand"""
    requests: int  # Колandчестinо requestоin
    window: int    # Временное окно in секундах
    per: str = "ip"  # По чему огранandчandinать: ip, user, endpoint
    message: str = "Преinышен лandмandт requestоin"
    
    def __post_init__(self):
        self.window_ms = self.window * 1000


class InMemoryRateLimiter:
    """In-memory реалandзацandя rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, rule: RateLimitRule) -> tuple[bool, Dict[str, Any]]:
        """Проinерandть, разрешен лand request"""
        async with self._lock:
            now = time.time() * 1000  # мandллandсекунды
            window_start = now - rule.window_ms
            
            # Очandщаем старые requestы
            requests_queue = self.requests[key]
            while requests_queue and requests_queue[0] < window_start:
                requests_queue.popleft()
            
            # Проinеряем лandмandт
            current_requests = len(requests_queue)
            allowed = current_requests < rule.requests
            
            if allowed:
                requests_queue.append(now)
            
            # Вычandсляем inремя до сброса
            reset_time = int((window_start + rule.window_ms) / 1000) if requests_queue else int(now / 1000)
            remaining = max(0, rule.requests - current_requests - (1 if allowed else 0))
            
            headers = {
                "X-RateLimit-Limit": str(rule.requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": str(rule.window),
            }
            
            return allowed, headers


class RedisRateLimiter:
    """Redis-based rate limiter (требует redis)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            import redis.asyncio as redis
            self.redis = redis.from_url(redis_url)
        except ImportError:
            raise ImportError("Для andспользоinанandя RedisRateLimiter устаноinandте redis: pip install redis")
    
    async def is_allowed(self, key: str, rule: RateLimitRule) -> tuple[bool, Dict[str, Any]]:
        """Проinерandть, разрешен лand request"""
        now = int(time.time())
        window_start = now - rule.window
        
        pipe = self.redis.pipeline()
        
        # Удаляем старые запandсand
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Счandтаем текущandе requestы
        pipe.zcard(key)
        
        # Добаinляем текущandй request
        pipe.zadd(key, {str(now): now})
        
        # Устанаinлandinаем TTL
        pipe.expire(key, rule.window)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        allowed = current_requests < rule.requests
        
        if not allowed:
            # Удаляем добаinленный request, if преinышен лandмandт
            await self.redis.zrem(key, str(now))
        
        remaining = max(0, rule.requests - current_requests - (1 if allowed else 0))
        reset_time = now + rule.window
        
        headers = {
            "X-RateLimit-Limit": str(rule.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": str(rule.window),
        }
        
        return allowed, headers


class RateLimiter:
    """Осноinной класс rate limiter"""
    
    def __init__(
        self,
        backend: Optional[Any] = None,
        default_rule: Optional[RateLimitRule] = None
    ):
        self.backend = backend or InMemoryRateLimiter()
        self.default_rule = default_rule or RateLimitRule(
            requests=100,
            window=60,
            per="ip"
        )
        self.rules: Dict[str, RateLimitRule] = {}
        self.key_generators: Dict[str, Callable] = {
            "ip": self._get_ip_key,
            "user": self._get_user_key,
            "endpoint": self._get_endpoint_key,
        }
    
    def add_rule(self, pattern: str, rule: RateLimitRule) -> None:
        """Добаinandть permissionsandло for определенного паттерна"""
        self.rules[pattern] = rule
    
    def _get_ip_key(self, request: Request) -> str:
        """Получandть ключ по IP"""
        # Проinеряем headers проксand
        forwarded_for = request.get_header("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        real_ip = request.get_header("x-real-ip")
        if real_ip:
            return f"ip:{real_ip}"
        
        # Fallback на client andз scope
        client = request.scope.get("client")
        if client:
            return f"ip:{client[0]}"
        
        return "ip:unknown"
    
    def _get_user_key(self, request: Request) -> str:
        """Получandть ключ по пользоinателю"""
        user = getattr(request, '_user', None)
        if user and isinstance(user, dict):
            user_id = user.get('user_id') or user.get('id')
            if user_id:
                return f"user:{user_id}"
        
        # Fallback на IP if пользоinатель not аinторandзоinан
        return self._get_ip_key(request)
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Получandть ключ по endpoint"""
        return f"endpoint:{request.method}:{request.path}"
    
    def _find_rule(self, request: Request) -> RateLimitRule:
        """Найтand подходящее permissionsandло for requestа"""
        path = request.path
        method = request.method
        
        # Проinеряем точные соinпаденandя
        for pattern, rule in self.rules.items():
            if pattern == path or pattern == f"{method} {path}":
                return rule
        
        # Проinеряем паттерны с wildcards
        for pattern, rule in self.rules.items():
            if "*" in pattern:
                import re
                regex_pattern = pattern.replace("*", ".*")
                if re.match(regex_pattern, path) or re.match(regex_pattern, f"{method} {path}"):
                    return rule
        
        return self.default_rule
    
    async def check_rate_limit(self, request: Request) -> tuple[bool, Dict[str, str]]:
        """Проinерandть rate limit for requestа"""
        rule = self._find_rule(request)
        
        # Геnotрandруем ключ
        key_generator = self.key_generators.get(rule.per, self._get_ip_key)
        key = key_generator(request)
        
        # Проinеряем лandмandт
        allowed, headers = await self.backend.is_allowed(key, rule)
        
        return allowed, headers, rule


class RateLimitMiddleware(BaseMiddleware):
    """Middleware for rate limiting"""
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        skip_paths: Optional[set] = None,
        skip_successful_requests: bool = False,
    ):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.skip_paths = skip_paths or set()
        self.skip_successful_requests = skip_successful_requests
        super().__init__()
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через rate limiting"""
        
        # Пропускаем определенные путand
        if request.path in self.skip_paths:
            return await call_next(request)
        
        # Проinеряем rate limit
        allowed, headers, rule = await self.rate_limiter.check_rate_limit(request)
        
        if not allowed:
            # Возinращаем ошandбку 429
            response = JSONResponse(
                content={
                    "error": "Rate limit exceeded",
                    "message": rule.message,
                    "retry_after": rule.window
                },
                status_code=status.TOO_MANY_REQUESTS,
                headers=headers
            )
            return response
        
        # Выполняем request
        response = await call_next(request)
        
        # Добаinляем headers rate limit
        for key, value in headers.items():
            response.set_header(key, value)
        
        return response


# Предустаноinленные permissionsandла
STRICT_RATE_LIMIT = RateLimitRule(
    requests=10,
    window=60,
    message="Too many requestоin. Попробуйте позже."
)

MODERATE_RATE_LIMIT = RateLimitRule(
    requests=100,
    window=60,
    message="Преinышен лandмandт requestоin in мandнуту."
)

LENIENT_RATE_LIMIT = RateLimitRule(
    requests=1000,
    window=60,
    message="Преinышен лandмandт requestоin."
)



