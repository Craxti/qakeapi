# -*- coding: utf-8 -*-
from pydantic import BaseModel

from qakeapi.core.application import Application
from qakeapi.core.dependencies import Dependency
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response


# Create models for documentation
class HelloResponse(BaseModel):
    message: str


class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    message: str


# Create application
app = Application(
    title="Basic Example",
    version="1.0.0",
    description="A basic example of QakeAPI application",
)


# Create dependency
class Config(Dependency):
    async def resolve(self):
        return {"app_name": "Basic Example", "version": "1.0.0"}


# Register dependency
config = Config()


# Define routes
@app.get("/", summary="Get index", description="Returns welcome message and config")
async def index(request: Request):
    return Response.json(
        {"message": "Welcome to QakeAPI!", "config": await config.resolve()}
    )


@app.get(
    "/hello/{name}",
    summary="Get hello message",
    description="Returns hello message with the provided name",
    response_model=HelloResponse,
)
async def hello(request: Request):
    name = request.path_params["name"]
    return Response.json({"message": f"Hello, {name}!"})


@app.post(
    "/echo",
    summary="Echo message",
    description="Returns the provided message",
    request_model=EchoRequest,
    response_model=EchoResponse,
)
async def echo(request: Request):
    data = await request.json()
    return Response.json({"message": data.get("message", "")})


if __name__ == "__main__":
    import uvicorn

    print("Starting server...")
    print("Available routes:", [(r.path, r.type, r.methods) for r in app.router.routes])
    uvicorn.run(app, host="0.0.0.0", port=8000)
