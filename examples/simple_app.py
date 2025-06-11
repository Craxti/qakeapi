from qakeapi.core.application import Application
from qakeapi.core.dependencies import Dependency, Inject
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
    await app.dependency_container.register(Dict[str, Any], data_store, scope="singleton")

# Добавляем middleware для логирования
@app.route.middleware()
def logging_middleware(handler):
    async def wrapper(request):
        print(f"Request: {request['method']} {request['path']}")
        response = await handler(request)
        print(f"Response: {response['status']}")
        return response
    return wrapper

# Добавляем маршруты
@app.api_route(
    "/",
    summary="Root endpoint",
    description="Returns a welcome message",
    response_model=Message,
    tags=["general"]
)
@Inject(app.dependency_container)
async def index(request, data: Dict[str, Any]):
    return {
        "status": 200,
        "headers": [(b"content-type", b"application/json")],
        "body": json.dumps({"message": "Hello, World!"}).encode()
    }

@app.api_route(
    "/items",
    methods=["GET", "POST"],
    summary="Manage items",
    description="Get all items or create a new item",
    tags=["items"],
    request_model=Item,
    response_model=ItemList
)
@Inject(app.dependency_container)
async def items(request, data: Dict[str, Any]):
    if request["method"] == "GET":
        items_list = [{"id": k, **v} for k, v in data.items()]
        return {
            "status": 200,
            "headers": [(b"content-type", b"application/json")],
            "body": json.dumps({"items": items_list}).encode()
        }
    else:  # POST
        item = json.loads(request["body"].decode())
        item_id = str(len(data) + 1)
        data[item_id] = item
        return {
            "status": 201,
            "headers": [(b"content-type", b"application/json")],
            "body": json.dumps({"id": item_id, **item}).encode()
        }

@app.api_route(
    "/items/{item_id}",
    summary="Get item by ID",
    description="Get a specific item by its ID",
    tags=["items"],
    response_model=ItemResponse
)
@Inject(app.dependency_container)
async def get_item(request, data: Dict[str, Any]):
    item_id = request["path_params"]["item_id"]
    if item_id not in data:
        return {
            "status": 404,
            "headers": [(b"content-type", b"application/json")],
            "body": json.dumps({"detail": "Item not found"}).encode()
        }
    return {
        "status": 200,
        "headers": [(b"content-type", b"application/json")],
        "body": json.dumps({"id": item_id, **data[item_id]}).encode()
    }

# Добавляем фоновую задачу
async def cleanup_task():
    while True:
        print("Running cleanup task...")
        await asyncio.sleep(60)

@app.on_startup
async def startup():
    await app.add_background_task(cleanup_task) 