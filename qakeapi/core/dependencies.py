"""
Dependency Injection system for QakeAPI.

This module provides dependency injection functionality to simplify
testing and dependency management.
"""

import inspect
from typing import Any, Callable, Dict, Optional, TypeVar, get_type_hints

from .hybrid import run_hybrid

T = TypeVar("T")


class Dependency:
    """
    Dependency wrapper for dependency injection.
    
    Allows functions to be used as dependencies that are automatically
    resolved when needed.
    """
    
    def __init__(self, func: Callable[..., Any], cache: bool = False):
        """
        Initialize dependency.
        
        Args:
            func: Dependency function
            cache: Whether to cache the result (default: False)
        """
        self.func = func
        self.cache = cache
        self._cached_value: Optional[Any] = None
        self._cached = False
    
    async def resolve(self, **kwargs: Any) -> Any:
        """
        Resolve dependency.
        
        Args:
            **kwargs: Arguments to pass to dependency function
            
        Returns:
            Resolved dependency value
        """
        if self.cache and self._cached:
            return self._cached_value
        
        result = await run_hybrid(self.func, **kwargs)
        
        if self.cache:
            self._cached_value = result
            self._cached = True
        
        return result
    
    def __call__(self, **kwargs: Any) -> Any:
        """Make dependency callable."""
        return self.resolve(**kwargs)


def Depends(dependency: Callable[..., Any], cache: bool = False) -> Dependency:
    """
    Dependency injection decorator.
    
    Args:
        dependency: Dependency function
        cache: Whether to cache the result (default: False)
        
    Returns:
        Dependency object
        
    Example:
        ```python
        def get_db():
            return Database()
        
        @app.get("/users")
        async def get_users(db = Depends(get_db)):
            return await db.get_users()
        ```
    """
    if isinstance(dependency, Dependency):
        return dependency
    
    return Dependency(dependency, cache=cache)


def resolve_dependencies(
    handler: Callable[..., Any],
    path_params: Dict[str, Any],
    query_params: Dict[str, Any],
    request: Any,
    body_data: Any = None,
) -> Dict[str, Any]:
    """
    Resolve dependencies for a handler function.
    
    Args:
        handler: Handler function
        path_params: Path parameters
        query_params: Query parameters
        request: Request object
        body_data: Request body data
        
    Returns:
        Dictionary of resolved dependencies
    """
    sig = inspect.signature(handler)
    dependencies: Dict[str, Any] = {}
    
    # Get type hints
    type_hints = get_type_hints(handler)
    
    for param_name, param in sig.parameters.items():
        # Skip if already provided
        if param_name in path_params or param_name in query_params:
            continue
        
        # Check if parameter is a Dependency
        if isinstance(param.default, Dependency):
            # Will be resolved later in async context
            dependencies[param_name] = param.default
        elif param_name == "request":
            dependencies[param_name] = request
        elif param_name == "body" and body_data is not None:
            dependencies[param_name] = body_data
        elif param.annotation == type(request) or param.annotation == Any:
            # Type hint suggests it's a request
            if param_name not in dependencies:
                dependencies[param_name] = request
    
    return dependencies


async def resolve_dependency_values(
    dependencies: Dict[str, Any],
    **context: Any,
) -> Dict[str, Any]:
    """
    Resolve dependency values asynchronously.
    
    Args:
        dependencies: Dictionary of dependencies
        **context: Context variables to pass to dependencies
        
    Returns:
        Dictionary of resolved dependency values
    """
    resolved: Dict[str, Any] = {}
    
    for name, dep in dependencies.items():
        if isinstance(dep, Dependency):
            resolved[name] = await dep.resolve(**context)
        else:
            resolved[name] = dep
    
    return resolved

