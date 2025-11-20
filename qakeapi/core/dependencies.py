"""
Dependency Injection system for QakeAPI
"""
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from functools import wraps

from .request import Request
from .exceptions import ValidationException

T = TypeVar("T")


class DependencyMarker:
    """Dependency marker"""

    def __init__(self, dependency: Callable[..., Any], use_cache: bool = True) -> None:
        self.dependency = dependency
        self.use_cache = use_cache


def Depends(dependency: Callable[..., Any], *, use_cache: bool = True) -> Any:
    """
    Dependency marker for injection into handler functions

    Args:
        dependency: Function or class for creating dependency
        use_cache: Whether to cache dependency result within request scope
    """
    return DependencyMarker(dependency, use_cache)


class DependencyResolver:
    """Dependency resolver"""

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._resolving: set = set()

    async def resolve_dependencies(
        self,
        func: Callable[..., Any],
        request: Request,
        path_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve all dependencies for function

        Args:
            func: Handler function
            request: HTTP request
            path_params: Path parameters

        Returns:
            Dictionary with resolved dependencies
        """
        signature = inspect.signature(func)
        resolved_params = {}
        path_params = path_params or {}

        for param_name, param in signature.parameters.items():
            if param_name in ["request", "req"]:
                # Automatically inject request object
                resolved_params[param_name] = request
            elif param_name in path_params:
                # Path parameters
                resolved_params[param_name] = path_params[param_name]
            elif isinstance(param.default, DependencyMarker):
                # Dependency marked through Depends()
                dependency_key = f"{param.default.dependency.__name__}_{id(param.default.dependency)}"

                if param.default.use_cache and dependency_key in self._cache:
                    resolved_params[param_name] = self._cache[dependency_key]
                else:
                    if dependency_key in self._resolving:
                        raise ValidationException(
                            f"Circular dependency detected: {param.default.dependency.__name__}"
                        )

                    self._resolving.add(dependency_key)
                    try:
                        resolved_value = await self._resolve_dependency(
                            param.default.dependency, request, path_params
                        )
                        if param.default.use_cache:
                            self._cache[dependency_key] = resolved_value
                        resolved_params[param_name] = resolved_value
                    finally:
                        self._resolving.discard(dependency_key)
            elif param.default != inspect.Parameter.empty:
                # Check query params first
                if param_name in request.query_params:
                    resolved_params[param_name] = request.get_query_param(param_name)
                else:
                    # Parameter with default value
                    resolved_params[param_name] = param.default
            elif param.annotation in [Request, "Request"]:
                # Typed request parameter
                resolved_params[param_name] = request
            else:
                # Check query params
                if param_name in request.query_params:
                    resolved_params[param_name] = request.get_query_param(param_name)
                elif param.default == inspect.Parameter.empty:
                    # If parameter is required and not found, try automatic resolution
                    if hasattr(param.annotation, "__call__"):
                        try:
                            resolved_value = await self._resolve_dependency(
                                param.annotation, request, path_params
                            )
                            resolved_params[param_name] = resolved_value
                        except Exception:
                            # If failed to resolve, skip
                            pass

        return resolved_params

    async def _resolve_dependency(
        self,
        dependency: Callable[..., Any],
        request: Request,
        path_params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Resolve specific dependency

        Args:
            dependency: Function or class dependency
            request: HTTP request
            path_params: Path parameters

        Returns:
            Resolved dependency
        """
        if inspect.isclass(dependency):
            # If it's a class, create instance without parameters
            # to avoid recursion
            try:
                return dependency()
            except TypeError:
                # If constructor requires params, return the class itself
                return dependency
        elif inspect.iscoroutinefunction(dependency):
            # Asynchronous function
            func_params = await self.resolve_dependencies(
                dependency, request, path_params
            )
            return await dependency(**func_params)
        elif callable(dependency):
            # Regular function
            func_params = await self.resolve_dependencies(
                dependency, request, path_params
            )
            return dependency(**func_params)
        else:
            # Return as is
            return dependency

    def clear_cache(self) -> None:
        """Clear dependency cache"""
        self._cache.clear()
        self._resolving.clear()


# Common dependencies


async def get_request_body(request: Request) -> bytes:
    """Get request body"""
    return await request.body()


async def get_request_json(request: Request) -> Any:
    """Get JSON from request"""
    return await request.json()


async def get_request_form(request: Request) -> Dict[str, Any]:
    """Get form data from request"""
    return await request.form()


def get_query_params(request: Request) -> Dict[str, Union[str, List[str]]]:
    """Get query parameters"""
    return request.query_params


def get_headers(request: Request) -> Dict[str, str]:
    """Get request headers"""
    return request.headers


def get_cookies(request: Request) -> Dict[str, str]:
    """Get cookies from request"""
    return request.cookies


# Decorator for automatic dependency injection
def inject_dependencies(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for automatic dependency injection
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Look for request object in arguments
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if request is None:
            # If request not found, call function as is
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        # Resolve dependencies
        resolver = DependencyResolver()
        dependencies = await resolver.resolve_dependencies(func, request)

        # Merge with existing kwargs
        final_kwargs = {**kwargs, **dependencies}

        if inspect.iscoroutinefunction(func):
            return await func(*args, **final_kwargs)
        else:
            return func(*args, **final_kwargs)

    return wrapper
