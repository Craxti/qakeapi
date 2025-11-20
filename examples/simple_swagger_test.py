"""
Простое тестовое приложение для проверки Swagger UI
"""
from qakeapi import QakeAPI

# Создаем простое приложение
app = QakeAPI(
    title="Simple Test API",
    description="Простое тестовое API для проверки Swagger UI",
    version="1.0.0",
    debug=True,
)


@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "Hello World"}


@app.get("/users")
async def get_users(limit: int = 10, offset: int = 0):
    """Получить список пользователей с пагинацией"""
    return {
        "users": [f"User {i}" for i in range(offset, offset + limit)],
        "limit": limit,
        "offset": offset,
    }


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Получить пользователя по ID"""
    return {"user_id": user_id, "name": f"User {user_id}"}


@app.get("/search")
async def search(q: str, category: str = None, limit: int = 10):
    """Поиск с параметрами"""
    return {
        "query": q,
        "category": category,
        "limit": limit,
        "results": [f"Result {i} for {q}" for i in range(limit)],
    }


if __name__ == "__main__":
    import uvicorn

    print("Запуск простого тестового API...")
    print("URL: http://localhost:8001")
    print("Docs: http://localhost:8001/docs")

    uvicorn.run(app, host="127.0.0.1", port=8001)
