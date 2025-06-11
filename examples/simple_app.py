from qakeapi.core.application import Application
from qakeapi.core.dependencies import Dependency, inject
from qakeapi.core.responses import Response
from qakeapi.core.requests import Request
from typing import Dict, Any, List
from pydantic import BaseModel
import json
import asyncio

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
    version="1.0.0"
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
    tags=["general"]
)
@inject(DataStore)
async def index(request: Request, data_store: DataStore):
    return Response.json({"message": "Hello, World!"})

@app.get(
    "/items",
    summary="Get all items",
    description="Get all items",
    response_model=ItemList,
    tags=["items"]
)
@inject(DataStore)
async def get_items(request: Request, data_store: DataStore):
    data = await data_store.resolve()
    items_list = [{"id": k, **v} for k, v in data.items()]
    return Response.json({"items": items_list})

@app.post(
    "/items",
    summary="Create new item",
    description="Create a new item",
    request_model=Item,
    response_model=ItemResponse,
    tags=["items"]
)
@inject(DataStore)
async def create_item(request: Request, data_store: DataStore):
    data = await data_store.resolve()
    item = await request.json()
    item_id = str(len(data) + 1)
    data[item_id] = item
    return Response.json({"id": item_id, **item}, status_code=201)

@app.get(
    "/items/{item_id}",
    summary="Get item by ID",
    description="Get a specific item by its ID",
    response_model=ItemResponse,
    tags=["items"]
)
@inject(DataStore)
async def get_item(request: Request, data_store: DataStore):
    data = await data_store.resolve()
    item_id = request.path_params["item_id"]
    if item_id not in data:
        return Response.json({"detail": "Item not found"}, status_code=404)
    return Response.json({"id": item_id, **data[item_id]})

# Добавляем фоновую задачу
async def cleanup_task():
    while True:
        print("Running cleanup task...")
        await asyncio.sleep(60)

@app.on_startup
async def startup():
    await app.add_background_task(cleanup_task) 