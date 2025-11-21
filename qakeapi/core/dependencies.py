"""
Dependency Injection system for the framework.

This module provides the Depends decorator and dependency resolution system.
"""

import inspect
import asyncio
from typing import Any, Callable, Dict, Optional, Type


class Dependency:
    """Represents a dependency with its resolver."""
    
    def __init__(
        self,
        dependency: Callable,
        use_cache: bool = True,
    ):
        """
        Initialize dependency.
        
        Args:
            dependency: Dependency function or class
            use_cache: Whether to cache dependency instances
        """
        self.dependency = dependency
        self.use_cache = use_cache
        self._cache: Optional[Any] = None
    
    def _convert_type(self, value: Any, target_type: Type) -> Any:
        """
        Convert value to target type if possible.
        
        Args:
            value: Value to convert
            target_type: Target type
            
        Returns:
            Converted value
        """
        if target_type == inspect.Parameter.empty:
            return value
        
        # If already correct type, return as is
        if isinstance(value, target_type):
            return value
        
        # Try to convert
        try:
            if target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            elif target_type == str:
                return str(value)
        except (ValueError, TypeError):
            # If conversion fails, return original value
            pass
        
        return value
    
    async def resolve(
        self,
        request: Any,
        path_params: Dict[str, Any],
        query_params: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """
        Resolve dependency.
        
        Args:
            request: Request object
            path_params: Path parameters
            query_params: Query parameters
            **kwargs: Additional arguments
            
        Returns:
            Resolved dependency value
        """
        # Use cache if available
        if self.use_cache and self._cache is not None:
            return self._cache
        
        # Get dependency signature
        sig = inspect.signature(self.dependency)
        params = {}
        
        # Resolve parameters
        for param_name, param in sig.parameters.items():
            param_type = param.annotation
            
            # Try to get from kwargs first
            if param_name in kwargs:
                params[param_name] = kwargs[param_name]
            # Try to get from path params
            elif param_name in path_params:
                value = path_params[param_name]
                # Try to convert type if needed
                params[param_name] = self._convert_type(value, param_type)
            # Try to get from query params
            elif param_name in query_params:
                value = query_params[param_name]
                # Try to convert type if needed
                params[param_name] = self._convert_type(value, param_type)
            # Try to inject Request
            elif param_type != inspect.Parameter.empty and inspect.isclass(param_type):
                # Check if it's a type hint for Request
                if hasattr(param_type, "__name__") and param_type.__name__ == "Request":
                    params[param_name] = request
                elif param.default != inspect.Parameter.empty:
                    params[param_name] = param.default
            # Use default if available
            elif param.default != inspect.Parameter.empty:
                params[param_name] = param.default
        
        # Call dependency
        if asyncio.iscoroutinefunction(self.dependency):
            result = await self.dependency(**params)
        else:
            result = self.dependency(**params)
        
        # Cache result if needed
        if self.use_cache:
            self._cache = result
        
        return result


def Depends(dependency: Callable, use_cache: bool = True) -> Dependency:
    """
    Mark a parameter as a dependency.
    
    Args:
        dependency: Dependency function or class
        use_cache: Whether to cache dependency instances
        
    Returns:
        Dependency instance
    """
    return Dependency(dependency, use_cache)


async def resolve_dependencies(
    handler: Callable,
    request: Any,
    path_params: Dict[str, Any],
    query_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve all dependencies for a handler.
    
    Args:
        handler: Handler function
        request: Request object
        path_params: Path parameters
        query_params: Query parameters
        
    Returns:
        Dictionary of resolved dependencies
    """
    sig = inspect.signature(handler)
    resolved = {}
    
    for param_name, param in sig.parameters.items():
        # Skip if already in path_params or query_params
        if param_name in path_params or param_name in query_params:
            continue
        
        # Check if it's a dependency
        if isinstance(param.default, Dependency):
            dependency = param.default
            resolved[param_name] = await dependency.resolve(
                request, path_params, query_params
            )
        # Try to inject Request
        elif param.annotation != inspect.Parameter.empty:
            param_type = param.annotation
            if hasattr(param_type, "__name__") and param_type.__name__ == "Request":
                resolved[param_name] = request
    
    return resolved
