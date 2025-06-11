from qakeapi.core.application import Application
from qakeapi.core.dependencies import Dependency, inject
from qakeapi.core.responses import Response
from qakeapi.core.requests import Request
from qakeapi.core.validation import RequestValidator, ResponseValidator
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
    message = Message(message="Hello, World!")
    return ResponseValidator.validate_response(message.dict(), Message)

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
    response_data = {"items": items_list}
    return ResponseValidator.validate_response(response_data, ItemList)

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
    request_data = await request.json()
    
    # Валидируем данные запроса
    validated_item = await RequestValidator.validate_request_body(request_data, Item)
    if validated_item is None:
        return Response.json({"detail": "Invalid request data"}, status_code=400)
    
    # Создаем новый элемент
    item_id = str(len(data) + 1)
    item_data = validated_item.dict()
    data[item_id] = item_data
    
    # Валидируем ответ
    response_data = {"id": item_id, **item_data}
    return ResponseValidator.validate_response(response_data, ItemResponse)

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
    uvicorn.run(app, host="0.0.0.0", port=8000) 