from qakeapi.core.application import Application
from qakeapi.core.responses import Response
from qakeapi.core.requests import Request
from qakeapi.core.dependencies import Dependency
from pydantic import BaseModel

# Создаем модели для документации
class HelloResponse(BaseModel):
    message: str

class EchoRequest(BaseModel):
    message: str

class EchoResponse(BaseModel):
    message: str

# Создаем приложение
app = Application(
    title="Basic Example",
    version="1.0.0",
    description="A basic example of QakeAPI application"
)

# Создаем зависимость
class Config(Dependency):
    async def resolve(self):
        return {
            "app_name": "Basic Example",
            "version": "1.0.0"
        }

# Регистрируем зависимость
config = Config()

# Определяем маршруты
@app.get("/", 
    summary="Get index",
    description="Returns welcome message and config"
)
async def index(request: Request):
    return Response.json({
        "message": "Welcome to QakeAPI!",
        "config": await config.resolve()
    })

@app.get("/hello/{name}",
    summary="Get hello message",
    description="Returns hello message with the provided name",
    response_model=HelloResponse
)
async def hello(request: Request):
    name = request.path_params["name"]
    return Response.json({"message": f"Hello, {name}!"})

@app.post("/echo",
    summary="Echo message",
    description="Returns the provided message",
    request_model=EchoRequest,
    response_model=EchoResponse
)
async def echo(request: Request):
    data = await request.json()
    return Response.json({"message": data.get("message", "")}) 