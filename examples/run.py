import uvicorn
from simple_app import app

if __name__ == "__main__":
    uvicorn.run(
        "simple_app:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    ) 