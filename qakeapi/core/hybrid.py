"""
Hybrid Executor - Automatic sync/async conversion.

This module provides functionality to automatically convert synchronous
functions to asynchronous ones, allowing seamless mixing of sync and async code.
"""

import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")

# Global thread pool executor for sync functions
_executor: ThreadPoolExecutor = None
_executor_shutdown = False


def _get_executor() -> ThreadPoolExecutor:
    """Get or create thread pool executor."""
    global _executor, _executor_shutdown
    
    if _executor is None or _executor_shutdown:
        _executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="qakeapi-sync")
        _executor_shutdown = False
    
    return _executor


def sync_to_async(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Convert a synchronous function to async.
    
    The function will be executed in a thread pool executor,
    allowing sync blocking code to run alongside async code.
    
    Args:
        func: Synchronous function to convert
        
    Returns:
        Async function wrapper
        
    Example:
        ```python
        def blocking_operation():
            time.sleep(1)  # Blocking
            return "done"
        
        async_func = sync_to_async(blocking_operation)
        result = await async_func()  # Runs in executor
        ```
    """
    if inspect.iscoroutinefunction(func):
        # Already async, return as is
        return func
    
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> T:
        """Async wrapper for sync function."""
        loop = asyncio.get_event_loop()
        executor = _get_executor()
        # Run sync function in thread pool
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
    
    return async_wrapper


def hybrid_executor(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Hybrid executor decorator.
    
    Automatically handles both sync and async functions:
    - If function is async, calls it directly
    - If function is sync, wraps it in executor
    
    Args:
        func: Function to wrap (can be sync or async)
        
    Returns:
        Async function wrapper
        
    Example:
        ```python
        @hybrid_executor
        def sync_handler(request):
            return {"status": "ok"}
        
        @hybrid_executor
        async def async_handler(request):
            return {"status": "ok"}
        
        # Both can be called with await
        result1 = await sync_handler(request)
        result2 = await async_handler(request)
        ```
    """
    if inspect.iscoroutinefunction(func):
        # Already async, return as is
        return func
    
    # Convert sync to async
    return sync_to_async(func)


async def run_hybrid(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Execute a function (sync or async) in the appropriate context.
    
    Args:
        func: Function to execute (can be sync or async)
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Function result
        
    Example:
        ```python
        def sync_func():
            return "sync"
        
        async def async_func():
            return "async"
        
        result1 = await run_hybrid(sync_func)  # Runs in executor
        result2 = await run_hybrid(async_func)  # Runs directly
        ```
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        # Sync function - run in executor
        loop = asyncio.get_event_loop()
        executor = _get_executor()
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


def shutdown_executor(wait: bool = True):
    """
    Shutdown the thread pool executor.
    
    Args:
        wait: If True, wait for all pending tasks to complete
        
    Note:
        After shutdown, executor will be recreated on next use.
    """
    global _executor, _executor_shutdown
    
    if _executor is not None and not _executor_shutdown:
        _executor.shutdown(wait=wait)
        _executor_shutdown = True
        _executor = None


