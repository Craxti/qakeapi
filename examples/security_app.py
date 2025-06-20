from qakeapi.core.application import Application
from qakeapi.security.cors import CORSMiddleware
from qakeapi.security.csrf import CSRFMiddleware

app = Application()

# Добавляем middleware для CORS и CSRF
cors_middleware = CORSMiddleware(
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
    allow_credentials=True
)

csrf_middleware = CSRFMiddleware(
    secret_key="your-secret-key",
    safe_methods=["GET", "HEAD", "OPTIONS"],
    cookie_secure=False  # Для тестирования локально
)

app.add_middleware(cors_middleware)
app.add_middleware(csrf_middleware)

@app.get("/")
async def index(request):
    return {"message": "Welcome to secured API!"}

@app.post("/api/data")
async def create_data(request):
    data = await request.json()
    return {"message": "Data created successfully", "data": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 