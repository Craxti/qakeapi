import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class BackgroundTask:
    """Класс для представления фоновой задачи"""

    def __init__(
        self,
        func: Callable,
        *args: Any,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        **kwargs: Any,
    ):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.task_id = task_id or str(id(self))
        self.timeout = timeout
        self.retry_count = retry_count
        self.retries = 0
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[Exception] = None
        self._task: Optional[asyncio.Task] = None

    async def run(self) -> Any:
        """Запуск задачи"""
        self.started_at = datetime.utcnow()
        try:
            if self.timeout:
                return await asyncio.wait_for(
                    self.func(*self.args, **self.kwargs), timeout=self.timeout
                )
            return await self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.error = e
            if self.retries < self.retry_count:
                self.retries += 1
                logger.warning(
                    f"Задача {self.task_id} завершилась с ошибкой, попытка {self.retries} из {self.retry_count}"
                )
                return await self.run()
            raise
        finally:
            self.completed_at = datetime.utcnow()


class BackgroundTaskManager:
    """Менеджер фоновых задач"""

    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Set[str] = set()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def add_task(self, task: BackgroundTask) -> str:
        """Добавление новой задачи"""
        self.tasks[task.task_id] = task
        asyncio.create_task(self._run_task(task))
        return task.task_id

    async def _run_task(self, task: BackgroundTask) -> None:
        """Запуск задачи"""
        self.running_tasks.add(task.task_id)
        try:
            task._task = asyncio.create_task(task.run())
            await task._task
        except asyncio.CancelledError:
            task.error = asyncio.CancelledError("Task was cancelled")
            task.completed_at = datetime.utcnow()
            logger.info(f"Задача {task.task_id} была отменена")
        except Exception as e:
            task.error = e
            logger.error(f"Ошибка в задаче {task.task_id}: {str(e)}")
        finally:
            self.running_tasks.remove(task.task_id)

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Получение задачи по ID"""
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получение статуса задачи"""
        task = self.get_task(task_id)
        if not task:
            return {"status": "not_found"}

        if task.completed_at:
            status = "completed" if not task.error else "failed"
        elif task.started_at:
            status = "running"
        else:
            status = "pending"

        return {
            "status": status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "error": str(task.error) if task.error else None,
            "retries": task.retries,
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Отмена задачи"""
        task = self.get_task(task_id)
        if task and task._task and not task._task.done():
            task._task.cancel()
            try:
                await task._task
            except asyncio.CancelledError:
                pass
            return True
        return False

    async def cleanup_old_tasks(self, max_age: timedelta = timedelta(hours=1)) -> None:
        """Очистка старых завершенных задач"""
        while True:
            now = datetime.utcnow()
            to_remove = [
                task_id
                for task_id, task in self.tasks.items()
                if task.completed_at and (now - task.completed_at) > max_age
            ]
            for task_id in to_remove:
                del self.tasks[task_id]
            await asyncio.sleep(300)  # Проверка каждые 5 минут

    async def start(self) -> None:
        """Запуск менеджера задач"""
        self._cleanup_task = asyncio.create_task(self.cleanup_old_tasks())

    async def stop(self) -> None:
        """Остановка менеджера задач"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        # Отмена всех запущенных задач
        for task_id in list(self.running_tasks):
            await self.cancel_task(task_id)
