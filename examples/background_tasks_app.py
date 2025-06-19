import asyncio
import time
import uuid
from typing import Dict

import uvicorn
from pydantic import BaseModel

from qakeapi import Application, Request, Response
from qakeapi.core.background import BackgroundTaskManager
from qakeapi.core.dependencies import Dependency


# Создаем модели для документации
class TaskRequest(BaseModel):
    duration: int = 10


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: str = None


class TaskStatus(BaseModel):
    status: str
    error: str = None


# Создаем приложение
app = Application(
    title="Background Tasks Example",
    version="1.0.0",
    description="An example of background tasks in QakeAPI",
)


# Создаем задачи
task_manager = BackgroundTaskManager()


@app.on_startup
async def startup():
    await task_manager.start()


@app.on_shutdown
async def shutdown():
    await task_manager.stop()


async def process_task(duration: int):
    await asyncio.sleep(duration)
    return f"Task completed after {duration} seconds"


@app.router.route("/tasks", methods=["POST"])
async def create_task(request: Request):
    """Создание новой фоновой задачи"""
    try:
        data = await request.json()
        task_request = TaskRequest(**data)
        task = task_manager.create_task(process_task(task_request.duration))
        return Response.json({"task_id": str(task.id), "status": "pending"})
    except Exception as e:
        return Response.json({"error": str(e)}, status=400)


@app.router.route("/tasks/{task_id}", methods=["GET"])
async def get_task(request: Request, task_id: str):
    """Получение статуса задачи"""
    task = task_manager.get_task(task_id)
    if not task:
        return Response.json({"error": "Task not found"}, status=404)
    
    status = "completed" if task.done() else "running"
    result = await task.result() if task.done() else None
    
    return Response.json({
        "task_id": task_id,
        "status": status,
        "result": result
    })


@app.router.route("/tasks", methods=["GET"])
async def list_tasks(request: Request):
    """Получение списка всех задач"""
    tasks = task_manager.list_tasks()
    return Response.json({
        str(task.id): {
            "task_id": str(task.id),
            "status": "completed" if task.done() else "running",
            "result": await task.result() if task.done() else None
        }
        for task in tasks
    })


@app.delete("/tasks/{task_id}")
async def cancel_task(request: Request):
    """Отмена задачи"""
    task_id = request.path_params["task_id"]
    if task_id not in task_manager.tasks:
        return Response.json(
            {"task_id": task_id, "message": "Task not found"},
            status_code=404
        )
    
    task = task_manager.tasks[task_id]
    if task["status"] in ["completed", "failed"]:
        return Response.json({
            "task_id": task_id,
            "message": f"Task already {task['status']}"
        })
    
    task["status"] = "cancelled"
    return Response.json({
        "task_id": task_id,
        "message": "Task cancelled successfully"
    })


# Пример задачи, которая может завершиться с ошибкой
async def failing_task() -> None:
    await asyncio.sleep(1)
    raise ValueError("Произошла ошибка в задаче")


@app.post(
    "/failing-task",
    summary="Create a failing task",
    description="Creates a task that will fail after 1 second",
    response_model=TaskResponse,
)
async def create_failing_task(request: Request):
    """Создание задачи, которая завершится с ошибкой"""
    task_id = await app.add_background_task(
        failing_task, retry_count=2  # Попробуем выполнить задачу 3 раза
    )

    return Response.json({"task_id": task_id, "message": "Failing task created"})


# Пример задачи с таймаутом
async def timeout_task() -> None:
    await asyncio.sleep(10)
    print("Эта строка не должна быть напечатана")


@app.post(
    "/timeout-task",
    summary="Create a timeout task",
    description="Creates a task that will timeout after 2 seconds",
    response_model=TaskResponse,
)
async def create_timeout_task(request: Request):
    """Создание задачи с таймаутом"""
    task_id = await app.add_background_task(
        timeout_task, timeout=2.0  # Задача будет отменена через 2 секунды
    )

    return Response.json({"task_id": task_id, "message": "Timeout task created"})


if __name__ == "__main__":
    from config import PORTS
    print("Starting background tasks example server...")
    uvicorn.run(app, host="0.0.0.0", port=PORTS['background_tasks_app'], log_level="debug")
