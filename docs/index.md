# QakeAPI

**Revolutionary Hybrid Async/Sync Web Framework for Python**

QakeAPI is the only Python web framework with true hybrid sync/async and **zero dependencies** in core. Write regular functions — the framework automatically converts them to async.

## Quick Start

```bash
pip install qakeapi
```

```python
from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(title="My API", version="1.3.1")
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": f"User {id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Visit `http://localhost:8000/docs` for Swagger UI.

## Documentation

- [Getting Started](getting-started.md)
- [Tutorial](tutorial.md)
- [API Reference](api-reference.md)
- [Benchmarks](benchmarks.md)
- [Migration from FastAPI](migration-from-fastapi.md)
