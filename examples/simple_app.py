# -*- coding: utf-8 -*-

import asyncio
import json
from typing import Any, Dict, List

from pydantic import BaseModel

from qakeapi.core.application import Application
from qakeapi.core.dependencies import Dependency, inject
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.core.validation import RequestValidator, ResponseValidator


# Модели данных
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


class ItemResponse(BaseModel):
    id: str
    name: str
    description: str = None
    price: float
    tax: float = None


class ItemList(BaseModel):
    items: List[ItemResponse]


class Message(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    detail: str


# Зависимость для хранения данных
class DataStore(Dependency):
    def __init__(self):
        super().__init__(scope="singleton")
        self.data = {}

    async def resolve(self) -> Dict[str, Any]:
        return self.data


# Создаем приложение
app = Application(
    title="Simple API",
    description="A simple API example with OpenAPI documentation",
    version="1.0.0",
)

# Регистрируем зависимости
data_store = DataStore()


@app.on_startup
async def register_dependencies():
    app.dependency_container.register(data_store)


# Добавляем middleware для логирования
@app.router.middleware()
def logging_middleware(handler):
    async def wrapper(request):
        print(f"Request: {request.method} {request.path}")
        response = await handler(request)
        print(f"Response: {response.status_code}")
        return response

    return wrapper


# Добавляем маршруты
@app.get(
    "/",
    summary="Root endpoint",
    description="Returns a welcome message",
    response_model=Message,
    tags=["general"],
)
@inject(DataStore)
async def index(request: Request, data_store: DataStore):
    message = Message(message="Hello, World!")
    return ResponseValidator.validate_response(message.dict(), Message)


@app.router.route("/items", methods=["GET", "POST"])
async def items(request: Request):
    data_store = await app.dependency_container.resolve(DataStore)
    
    if request.method == "GET":
        items_list = [{"id": k, **v} for k, v in data_store.items()]
        response_data = {"items": items_list}
        return Response.json(response_data)
    
    elif request.method == "POST":
        request_data = await request.json()
        
        # Валидируем данные запроса
        validated_item = await RequestValidator.validate_request_body(request_data, Item)
        if validated_item is None:
            return Response.json({"detail": "Invalid request data"}, status_code=400)
            
        # Создаем новый элемент
        item_id = str(len(data_store) + 1)
        item_data = validated_item.model_dump()
        data_store[item_id] = item_data
        
        # Возвращаем ответ
        response_data = {"id": item_id, **item_data}
        return Response.json(response_data)


@app.get(
    "/items/{item_id}",
    summary="Get item by ID",
    description="Get a specific item by its ID",
    response_model=ItemResponse,
    tags=["items"],
)
@inject(DataStore)
async def get_item(request: Request, data_store: DataStore):
    data = data_store
    item_id = request.path_params["item_id"]

    if item_id not in data:
        return Response.json({"detail": "Item not found"}, status_code=404)

    response_data = {"id": item_id, **data[item_id]}
    return ResponseValidator.validate_response(response_data, ItemResponse)


# Добавляем фоновую задачу
async def cleanup_task():
    while True:
        print("Running cleanup task...")
        await asyncio.sleep(60)


@app.on_startup
async def startup():
    await app.add_background_task(cleanup_task)


if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    uvicorn.run(app, host="0.0.0.0", port=PORTS['simple_app'])
