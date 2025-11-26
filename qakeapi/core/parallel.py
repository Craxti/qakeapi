"""
Parallel Resolver - Parallel dependency resolution.

This module provides functionality to resolve dependencies in parallel,
automatically detecting independent dependencies and executing them concurrently.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")


class ParallelResolver:
    """
    Parallel dependency resolver.
    
    Automatically resolves dependencies in parallel when possible,
    detecting independent dependencies and executing them concurrently.
    """
    
    def __init__(self):
        """Initialize parallel resolver."""
        pass
    
    async def resolve_parallel(
        self,
        dependencies: Dict[str, Callable[..., Any]],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Resolve dependencies in parallel.
        
        Args:
            dependencies: Dictionary of {name: dependency_function}
            context: Optional context dictionary
            
        Returns:
            Dictionary of {name: resolved_value}
            
        Example:
            ```python
            async def get_user():
                return {"id": 1, "name": "John"}
            
            async def get_stats():
                return {"views": 100}
            
            resolver = ParallelResolver()
            results = await resolver.resolve_parallel({
                "user": get_user,
                "stats": get_stats
            })
            # Both functions execute in parallel!
            ```
        """
        if context is None:
            context = {}
        
        # Create tasks for all dependencies
        tasks = {}
        for name, dep_func in dependencies.items():
            # Check if dependency is async or sync
            if asyncio.iscoroutinefunction(dep_func):
                tasks[name] = dep_func(**context)
            else:
                # Sync function - run in executor
                loop = asyncio.get_event_loop()
                tasks[name] = loop.run_in_executor(
                    None, lambda f=dep_func: f(**context)
                )
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Build result dictionary
        result_dict = {}
        for (name, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                raise result
            result_dict[name] = result
        
        return result_dict


def parallel(*dependencies: Callable[..., Any]):
    """
    Parallel decorator - marks dependencies to be resolved in parallel.
    
    Args:
        *dependencies: Dependency functions to resolve in parallel
        
    Example:
        ```python
        async def fetch_user():
            return {"id": 1}
        
        async def fetch_stats():
            return {"views": 100}
        
        @app.get("/dashboard")
        async def dashboard(
            user = parallel(fetch_user),
            stats = parallel(fetch_stats)
        ):
            # user and stats are resolved in parallel!
            return {"user": user, "stats": stats}
        ```
    """
    # This is a marker - actual resolution happens in parameter extraction
    return dependencies


# Global resolver instance
_resolver = ParallelResolver()


async def resolve_parallel(
    dependencies: Dict[str, Callable[..., Any]], context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Resolve dependencies in parallel.
    
    Args:
        dependencies: Dictionary of {name: dependency_function}
        context: Optional context dictionary
        
    Returns:
        Dictionary of {name: resolved_value}
    """
    return await _resolver.resolve_parallel(dependencies, context)


