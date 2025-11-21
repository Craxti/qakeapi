# Quick Start Guide

Get started with QakeAPI in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/qakeapi/qakeapi.git
cd qakeapi

# Install in development mode
pip install -e .

# Install uvicorn for running the server
pip install uvicorn
```

## Your First API

Create a file `main.py`:

```python
from qakeapi import QakeAPI

app = QakeAPI(title="My First API")

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
async def get_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run it:

```bash
python main.py
```

Visit http://localhost:8000 - you'll see `{"message": "Hello, World!"}`

Visit http://localhost:8000/docs - you'll see the interactive API documentation!

## Common Patterns

### Handling POST Requests

```python
from qakeapi import QakeAPI, Request

app = QakeAPI()

@app.post("/items")
async def create_item(request: Request):
    data = await request.json()
    return {"created": data}
```

### Using Validation

```python
from qakeapi import QakeAPI
from qakeapi.validation import BaseModel, Field, StringValidator, IntegerValidator

app = QakeAPI()

class ItemCreate(BaseModel):
    name: str = Field(validator=StringValidator(min_length=1, max_length=100))
    price: float = Field(validator=FloatValidator(min_value=0.0))
    quantity: int = Field(validator=IntegerValidator(min_value=0))

@app.post("/items")
async def create_item(item: ItemCreate):
    return {"item": item.dict()}
```

### Dependency Injection

```python
from qakeapi import QakeAPI, Depends

app = QakeAPI()

async def get_database():
    return {"connected": True}

@app.get("/")
async def root(db: dict = Depends(get_database)):
    return {"database": db}
```

### WebSocket

```python
from qakeapi import QakeAPI, WebSocket

app = QakeAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Connected!"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
```

### Authentication

```python
from qakeapi import QakeAPI, Request
from qakeapi.security import AuthManager

app = QakeAPI()
auth_manager = AuthManager(secret_key="your-secret-key")

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    # Verify credentials here
    token = auth_manager.create_access_token({"user_id": 1})
    return {"access_token": token}
```

## Testing

```python
from qakeapi import QakeAPI
from qakeapi.testing import TestClient

app = QakeAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

# Test
def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
```

## Next Steps

- Read the [Complete Guide](docs/GUIDE.md) for detailed documentation
- Check the [API Reference](docs/API_REFERENCE.md) for all available features
- Explore the [examples](examples/) directory for more examples
- See [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md) for architecture details

## Need Help?

- Check the documentation in `docs/` directory
- Look at examples in `examples/` directory
- Read the source code - it's well documented!

Happy coding!

