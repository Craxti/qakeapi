"""
Пример использования валидации данных в QakeAPI
"""
from qakeapi import (
    QakeAPI, Request, JSONResponse,
    DataValidator, StringValidator, IntegerValidator, FloatValidator,
    BooleanValidator, EmailValidator, ListValidator, validate_json
)
from qakeapi.core.exceptions import ValidationException
from qakeapi.middleware.cors import CORSMiddleware

# Создаем приложение
app = QakeAPI(
    title="Пример валидации данных",
    description="Демонстрация системы валидации QakeAPI",
    version="1.0.0",
    debug=True,
)

# Добавляем CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Создаем валидаторы
user_validator = DataValidator({
    "name": StringValidator(min_length=2, max_length=50),
    "email": EmailValidator(),
    "age": IntegerValidator(min_value=0, max_value=150, required=False),
    "bio": StringValidator(max_length=500, required=False),
})

product_validator = DataValidator({
    "title": StringValidator(min_length=1, max_length=200),
    "price": FloatValidator(min_value=0),
    "description": StringValidator(max_length=1000, required=False),
    "tags": ListValidator(
        item_validator=StringValidator(max_length=30),
        max_items=10,
        required=False
    ),
    "category_id": IntegerValidator(min_value=1),
})

# Фиктивная база данных
users_db = []
products_db = []
categories_db = [
    {"id": 1, "name": "Электроника"},
    {"id": 2, "name": "Одежда"},
    {"id": 3, "name": "Книги"},
    {"id": 4, "name": "Спорт"},
]


@app.get("/")
async def root():
    """Главная страница с информацией о валидации"""
    return {
        "message": "Пример валидации данных в QakeAPI",
        "features": [
            "Автоматическая валидация входных данных",
            "Подробные сообщения об ошибках",
            "Поддержка различных типов данных",
            "Кастомные валидаторы",
            "Интеграция с Pydantic (опционально)"
        ],
        "endpoints": {
            "users": {
                "POST /users/": "Создать пользователя (с валидацией)",
                "GET /users/": "Получить список пользователей"
            },
            "products": {
                "POST /products/": "Создать продукт (с валидацией)",
                "GET /products/": "Получить список продуктов"
            },
            "validation": {
                "POST /validate/user": "Проверить данные пользователя",
                "POST /validate/product": "Проверить данные продукта"
            }
        }
    }


# Пользователи
@app.post("/users/")
async def create_user(request: Request):
    """
    Создать пользователя с валидацией данных
    
    Ожидаемые поля:
    - name: строка от 2 до 50 символов (обязательно)
    - email: валидный email адрес (обязательно)
    - age: целое число от 0 до 150 (опционально)
    - bio: строка до 500 символов (опционально)
    """
    try:
        data = await request.json()
    except Exception:
        raise ValidationException("Invalid JSON format")
    
    # Валидируем данные
    result = user_validator.validate(data)
    if not result.is_valid:
        raise ValidationException({
            "message": "Validation failed",
            "errors": result.errors,
            "received_data": data
        })
    
    # Проверяем уникальность email
    for user in users_db:
        if user["email"] == result.data["email"]:
            raise ValidationException("User with this email already exists")
    
    # Создаем пользователя
    new_user = {
        "id": len(users_db) + 1,
        **result.data
    }
    users_db.append(new_user)
    
    return {
        "message": "User created successfully",
        "user": new_user
    }


@app.get("/users/")
async def get_users():
    """Получить список всех пользователей"""
    return {
        "users": users_db,
        "total": len(users_db)
    }


# Продукты
@app.post("/products/")
async def create_product(request: Request):
    """
    Создать продукт с валидацией данных
    
    Ожидаемые поля:
    - title: строка от 1 до 200 символов (обязательно)
    - price: положительное число (обязательно)
    - description: строка до 1000 символов (опционально)
    - tags: список строк до 30 символов каждая, максимум 10 тегов (опционально)
    - category_id: ID существующей категории (обязательно)
    """
    try:
        data = await request.json()
    except Exception:
        raise ValidationException("Invalid JSON format")
    
    # Валидируем данные
    result = product_validator.validate(data)
    if not result.is_valid:
        raise ValidationException({
            "message": "Validation failed",
            "errors": result.errors,
            "received_data": data
        })
    
    # Проверяем существование категории
    category_exists = any(cat["id"] == result.data["category_id"] for cat in categories_db)
    if not category_exists:
        raise ValidationException(f"Category with ID {result.data['category_id']} does not exist")
    
    # Создаем продукт
    new_product = {
        "id": len(products_db) + 1,
        **result.data
    }
    products_db.append(new_product)
    
    return {
        "message": "Product created successfully",
        "product": new_product
    }


@app.get("/products/")
async def get_products():
    """Получить список всех продуктов"""
    return {
        "products": products_db,
        "total": len(products_db)
    }


@app.get("/categories/")
async def get_categories():
    """Получить список категорий"""
    return {
        "categories": categories_db,
        "total": len(categories_db)
    }


# Endpoints для тестирования валидации
@app.post("/validate/user")
async def validate_user_data(request: Request):
    """
    Проверить данные пользователя без создания
    
    Возвращает результат валидации и очищенные данные.
    """
    try:
        data = await request.json()
    except Exception:
        raise ValidationException("Invalid JSON format")
    
    result = user_validator.validate(data)
    
    return {
        "is_valid": result.is_valid,
        "errors": result.errors if not result.is_valid else None,
        "validated_data": result.data if result.is_valid else None,
        "original_data": data
    }


@app.post("/validate/product")
async def validate_product_data(request: Request):
    """
    Проверить данные продукта без создания
    
    Возвращает результат валидации и очищенные данные.
    """
    try:
        data = await request.json()
    except Exception:
        raise ValidationException("Invalid JSON format")
    
    result = product_validator.validate(data)
    
    return {
        "is_valid": result.is_valid,
        "errors": result.errors if not result.is_valid else None,
        "validated_data": result.data if result.is_valid else None,
        "original_data": data
    }


# Пример использования декоратора валидации
@validate_json(user_validator)
@app.post("/users/with-decorator")
async def create_user_with_decorator(request: Request, validated_data: dict):
    """
    Создать пользователя используя декоратор валидации
    
    Декоратор @validate_json автоматически валидирует JSON данные
    и передает их в параметр validated_data.
    """
    # Проверяем уникальность email
    for user in users_db:
        if user["email"] == validated_data["email"]:
            raise ValidationException("User with this email already exists")
    
    # Создаем пользователя
    new_user = {
        "id": len(users_db) + 1,
        **validated_data
    }
    users_db.append(new_user)
    
    return {
        "message": "User created successfully with decorator",
        "user": new_user
    }


# Пример сложной валидации
complex_validator = DataValidator({
    "user": DataValidator({
        "name": StringValidator(min_length=2, max_length=50),
        "email": EmailValidator(),
        "preferences": DataValidator({
            "theme": StringValidator(),
            "notifications": DataValidator({
                "email": BooleanValidator(),
                "push": BooleanValidator(),
            })
        })
    }),
    "products": ListValidator(
        item_validator=DataValidator({
            "title": StringValidator(min_length=1, max_length=100),
            "quantity": IntegerValidator(min_value=1),
        }),
        min_items=1,
        max_items=10
    )
})


@app.post("/complex-validation")
async def complex_validation_example(request: Request):
    """
    Пример сложной вложенной валидации
    
    Ожидает объект с пользователем и списком продуктов.
    """
    try:
        data = await request.json()
    except Exception:
        raise ValidationException("Invalid JSON format")
    
    result = complex_validator.validate(data)
    if not result.is_valid:
        raise ValidationException({
            "message": "Complex validation failed",
            "errors": result.errors,
            "received_data": data
        })
    
    return {
        "message": "Complex validation passed",
        "validated_data": result.data,
        "summary": {
            "user_name": result.data["user"]["name"],
            "user_email": result.data["user"]["email"],
            "products_count": len(result.data["products"]),
            "total_quantity": sum(p["quantity"] for p in result.data["products"])
        }
    }


# Обработчик ошибок валидации
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Кастомный обработчик ошибок валидации"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.detail if hasattr(exc, 'detail') else str(exc),
            "path": request.path,
            "method": request.method,
            "help": "Check the API documentation for correct data format"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print("🔍 Запуск примера валидации данных QakeAPI")
    print("📚 Документация: http://localhost:8000/docs")
    print("🧪 Тестовые данные:")
    print("   Пользователь: POST /users/ с {\"name\": \"Иван\", \"email\": \"ivan@example.com\", \"age\": 25}")
    print("   Продукт: POST /products/ с {\"title\": \"Ноутбук\", \"price\": 50000, \"category_id\": 1}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
