# Getting Started with QakeAPI

This guide will help you get started with QakeAPI, from installation to creating your first application.

## Installation

QakeAPI can be installed using pip:

```bash
pip install qakeapi
```

## Basic Usage

Here's a simple example of a QakeAPI application:

```python
from qakeapi import Application

app = Application()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run()
```

## Creating Your First Application

1. Create a new file `app.py`:

```python
from qakeapi import Application
from qakeapi.core.responses import Response

app = Application(
    title="My First API",
    version="1.0.0"
)

@app.get("/")
async def home():
    return Response.json({"message": "Welcome to my API!"})

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return Response.json({"item_id": item_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

2. Run the application:

```bash
python app.py
```

3. Visit `http://localhost:8000/docs` to see the automatic API documentation.

## Key Features to Try

1. **Path Parameters**:
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

2. **Query Parameters**:
```python
@app.get("/search")
async def search(q: str = None):
    return {"query": q}
```

3. **Request Body**:
```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
async def create_item(item: Item):
    return {"item": item.dict()}
```

## Next Steps

- Learn about [Core Concepts](Core-Concepts)
- Explore [Features](Features)
- Check out [Examples](Examples)
- Read [Best Practices](Best-Practices)

## Need Help?

- Check the [GitHub Issues](https://github.com/Craxti/qakeapi/issues)
- Join our [Discussions](https://github.com/Craxti/qakeapi/discussions)
- Read the [FAQ](FAQ) 