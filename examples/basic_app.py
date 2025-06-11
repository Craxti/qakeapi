from qakeapi.core.application import Application
from qakeapi.core.responses import Response
from qakeapi.core.requests import Request
from qakeapi.core.dependencies import Dependency

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
@app.get("/")
async def index(request: Request):
    return Response.json({
        "message": "Welcome to QakeAPI!",
        "config": await config.resolve()
    })

@app.get("/hello/{name}")
async def hello(request: Request, name: str):
    return Response.text(f"Hello, {name}!")

@app.post("/echo")
async def echo(request: Request):
    data = await request.json()
    return Response.json(data) 