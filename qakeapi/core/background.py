"""
Background tasks system for QakeAPI.

This module provides functionality for running tasks in the background,
independent of the request/response cycle.
"""

import asyncio
import inspect
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .hybrid import run_hybrid


class BackgroundTask:
    """Represents a background task."""
    
    def __init__(
        self,
        func: Callable[..., Any],
        *args: Any,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize background task.
        
        Args:
            func: Task function
            *args: Positional arguments
            task_id: Optional task ID
            **kwargs: Keyword arguments
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.task_id = task_id or str(uuid4())
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[Exception] = None
        self._task: Optional[asyncio.Task] = None
    
    async def run(self) -> Any:
        """Run task."""
        self.started_at = datetime.utcnow()
        try:
            result = await run_hybrid(self.func, *self.args, **self.kwargs)
            self.result = result
            self.completed_at = datetime.utcnow()
            return result
        except Exception as e:
            self.error = e
            self.completed_at = datetime.utcnow()
            raise


class BackgroundTaskManager:
    """Manager for background tasks."""
    
    def __init__(self):
        """Initialize background task manager."""
        self.tasks: Dict[str, BackgroundTask] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_task(
        self,
        func: Callable[..., Any],
        *args: Any,
        task_id: Optional[str] = None,
        wait: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Add background task.
        
        Args:
            func: Task function
            *args: Positional arguments
            task_id: Optional task ID
            wait: Whether to wait for task completion
            **kwargs: Keyword arguments
            
        Returns:
            Task ID
            
        Example:
            ```python
            async def send_email(user_id):
                # Send email logic
                pass
            
            task_id = await background_manager.add_task(send_email, user_id=1)
            ```
        """
        task = BackgroundTask(func, *args, task_id=task_id, **kwargs)
        self.tasks[task.task_id] = task
        
        # Create and run task
        async def run_task():
            try:
                await task.run()
            except Exception as e:
                # Error already stored in task
                pass
            finally:
                if task.task_id in self._running_tasks:
                    del self._running_tasks[task.task_id]
        
        coro = run_task()
        asyncio_task = asyncio.create_task(coro)
        self._running_tasks[task.task_id] = asyncio_task
        
        if wait:
            await asyncio_task
        
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status."""
        task = self.get_task(task_id)
        if task is None:
            return {"status": "not_found"}
        
        status = "running"
        if task.completed_at:
            status = "completed" if task.error is None else "failed"
        
        return {
            "task_id": task.task_id,
            "status": status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": str(task.error) if task.error else None,
        }


# Global background task manager
_background_manager = BackgroundTaskManager()


def background_task(func: Callable[..., Any]):
    """
    Decorator for background task function.
    
    Example:
        ```python
        @background_task
        async def send_notification(user_id: int):
            # Background task logic
            pass
        
        # Run in background
        await send_notification(user_id=1)
        ```
    """
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        """Wrapper that runs function in background."""
        return await _background_manager.add_task(func, *args, **kwargs)
    
    return wrapper


async def add_background_task(
    func: Callable[..., Any], *args: Any, task_id: Optional[str] = None, **kwargs: Any
) -> str:
    """
    Add background task.
    
    Args:
        func: Task function
        *args: Positional arguments
        task_id: Optional task ID
        **kwargs: Keyword arguments
        
    Returns:
        Task ID
        
    Example:
        ```python
        async def send_email(email: str):
            # Send email logic
            pass
        
        task_id = await add_background_task(send_email, "user@example.com")
        ```
    """
    return await _background_manager.add_task(func, *args, task_id=task_id, **kwargs)

