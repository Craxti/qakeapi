"""
Базовая демонстрация QakeAPI
"""
from qakeapi import QakeAPI

# Создаем приложение
app = QakeAPI(
    title="QakeAPI Basic Demo",
    version="1.0.0",
    debug=True,
)


@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "QakeAPI работает!", "version": "1.0.0", "status": "OK"}


@app.get("/test")
async def test():
    """Тестовый endpoint"""
    return {"test": "success"}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Получить item по ID"""
    return {"item_id": item_id, "name": f"Item {item_id}"}


if __name__ == "__main__":
    import uvicorn

    print("Запуск базового демо...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
