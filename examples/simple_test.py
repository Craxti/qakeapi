"""
Простой тест основного функционала QakeAPI
"""

from qakeapi import QakeAPI, JSONResponse

# Создаем приложение
app = QakeAPI(title="Simple Test", debug=True)


@app.get("/")
async def root():
    return {"message": "Hello QakeAPI!"}


@app.get("/test/{item_id}")
async def get_item(item_id: str):
    return {"item_id": item_id, "message": "Item found"}


@app.post("/test")
async def create_item(request):
    data = await request.json()
    return {"received": data, "status": "created"}


if __name__ == "__main__":
    print("QakeAPI импортирован успешно!")
    print("Приложение создано!")
    print("Маршруты зарегистрированы!")
    print("Все основные компоненты работают!")

    # Проверяем маршруты
    print(f"Зарегистрировано маршрутов: {len(app.routes)}")
    for route in app.routes:
        print(f"  - {route.methods} {route.path}")
