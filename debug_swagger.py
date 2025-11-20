"""
Отладочное приложение для проверки Swagger UI
"""
from qakeapi import QakeAPI

app = QakeAPI(
    title="Debug Swagger API",
    description="Отладочное API для проверки параметров",
    version="1.0.0",
    debug=True
)

@app.get("/test")
async def test_params(name: str, age: int = 25, active: bool = True):
    """Тестовый эндпоинт с разными типами параметров"""
    return {
        "name": name,
        "age": age, 
        "active": active,
        "message": f"Hello {name}, you are {age} years old"
    }

@app.get("/users/{user_id}")
async def get_user_by_id(user_id: int):
    """Получить пользователя по ID"""
    return {"user_id": user_id, "name": f"User {user_id}"}

if __name__ == "__main__":
    import uvicorn
    print("Debug API started!")
    print("Endpoints:")
    print("   GET /test?name=John&age=30&active=true")
    print("   GET /users/123")
    print("Swagger UI: http://localhost:8002/docs")
    print("ReDoc: http://localhost:8002/redoc")
    
    uvicorn.run(app, host="127.0.0.1", port=8002)
