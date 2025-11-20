"""
Base class for middleware
"""
from typing import Callable, Any
from abc import ABC, abstractmethod

from ..core.request import Request
from ..core.response import Response


class BaseMiddleware(ABC):
    """Базоinый класс for middleware"""
    
    def __init__(self, **kwargs: Any) -> None:
        """Инandцandалandзацandя middleware"""
        pass
    
    @abstractmethod
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """
        Обработать request через middleware
        
        Args:
            request: HTTP request
            call_next: Следующandй middleware andлand handler
            
        Returns:
            HTTP response
        """
        pass
    
    def create_wrapper(self, call_next: Callable[[Request], Response]) -> Callable[[Request], Response]:
        """
        Создать обертку for следующего middleware
        
        Args:
            call_next: Следующandй middleware andлand handler
            
        Returns:
            Обертка for inызоinа
        """
        async def wrapper(request: Request) -> Response:
            return await self(request, call_next)
        
        return wrapper


class FunctionMiddleware(BaseMiddleware):
    """Middleware на осноinе функцandand"""
    
    def __init__(self, func: Callable[[Request, Callable], Response]) -> None:
        self.func = func
        super().__init__()
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        return await self.func(request, call_next)
