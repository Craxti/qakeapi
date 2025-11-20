# 🚀 Быстрый старт QakeAPI

Добро пожаловать в QakeAPI! Этот гид поможет вам быстро начать работу с фреймворком.

## 📦 Установка

```bash
# Основные зависимости
pip install uvicorn pydantic jinja2 python-multipart

# Для разработки и тестирования
pip install pytest pytest-asyncio httpx black isort mypy
```

## 🏃‍♂️ Запуск примеров

### 1. Базовое приложение

```bash
python examples/basic_app.py
```

Откройте http://localhost:8000 в браузере.

### 2. Продвинутое приложение с аутентификацией

```bash
python examples/advanced_app.py
```

Особенности:
- JWT аутентификация
- Валидация данных с Pydantic
- WebSocket чат
- API ключи

### 3. Веб-приложение с шаблонами

```bash
python examples/web_app.py
```

Особенности:
- HTML шаблоны
- Статические файлы
- Формы
- Красивый интерфейс

### 4. Пример валидации данных

```bash
python examples/validation_example.py
```

Особенности:
- Встроенная система валидации
- Подробные сообщения об ошибках
- Сложная вложенная валидация

### 5. Демонстрационное приложение

```bash
python app.py
```

Полнофункциональное API с документацией.

## 📚 Документация API

После запуска любого примера, документация доступна по адресам:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI схема**: http://localhost:8000/openapi.json

## 🧪 Тестирование

Запуск всех тестов:

```bash
pytest tests/ -v
```

Запуск конкретного теста:

```bash
pytest tests/test_basic.py -v
pytest tests/test_middleware.py -v
pytest tests/test_websocket.py -v
```

## 🔧 Создание своего приложения

### Минимальный пример

```python
from qakeapi import QakeAPI

app = QakeAPI(title="Мое API")

@app.get("/")
async def root():
    return {"message": "Привет, мир!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### С валидацией данных

```python
from qakeapi import QakeAPI, DataValidator, StringValidator, IntegerValidator

app = QakeAPI(title="API с валидацией")

# Создаем валидатор
user_validator = DataValidator({
    "name": StringValidator(min_length=2, max_length=50),
    "age": IntegerValidator(min_value=0, max_value=150),
})

@app.post("/users/")
async def create_user(request):
    data = await request.json()
    
    # Валидируем данные
    result = user_validator.validate(data)
    if not result.is_valid:
        return {"errors": result.errors}, 400
    
    return {"message": "Пользователь создан", "user": result.data}
```

### С middleware

```python
from qakeapi import QakeAPI
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware

app = QakeAPI(title="API с middleware")

# Добавляем CORS
app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
))

# Добавляем логирование
app.add_middleware(LoggingMiddleware())

@app.get("/")
async def root():
    return {"message": "API с middleware"}
```

### С WebSocket

```python
from qakeapi import QakeAPI, WebSocket

app = QakeAPI(title="API с WebSocket")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        pass
```

## 🛠️ Полезные команды

### Форматирование кода

```bash
black qakeapi/ examples/ tests/
isort qakeapi/ examples/ tests/
```

### Проверка типов

```bash
mypy qakeapi/
```

### Запуск с автоперезагрузкой

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Запуск в продакшене

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Структура проекта

```
qakeapi/
├── qakeapi/                 # Основной пакет фреймворка
│   ├── core/               # Ядро фреймворка
│   │   ├── application.py  # Основной класс приложения
│   │   ├── request.py      # Обработка HTTP запросов
│   │   ├── response.py     # HTTP ответы
│   │   ├── router.py       # Система маршрутизации
│   │   ├── websocket.py    # WebSocket поддержка
│   │   ├── dependencies.py # Система зависимостей
│   │   └── exceptions.py   # Исключения
│   ├── middleware/         # Middleware компоненты
│   │   ├── base.py        # Базовый класс middleware
│   │   ├── cors.py        # CORS middleware
│   │   ├── logging.py     # Логирование
│   │   └── auth.py        # Аутентификация
│   └── utils/             # Утилиты
│       ├── status.py      # HTTP статус коды
│       ├── static.py      # Статические файлы
│       ├── templates.py   # Шаблоны
│       └── validation.py  # Валидация данных
├── examples/              # Примеры использования
├── tests/                # Тесты
├── app.py               # Демонстрационное приложение
├── pyproject.toml       # Конфигурация проекта
└── README.md           # Документация
```

## 🤝 Получение помощи

- 📖 Читайте README.md для подробной документации
- 🔍 Изучайте примеры в папке examples/
- 🧪 Смотрите тесты для понимания API
- 📚 Используйте автоматическую документацию /docs

## 🎯 Следующие шаги

1. Запустите базовый пример
2. Изучите документацию API
3. Попробуйте создать свое приложение
4. Добавьте middleware по необходимости
5. Настройте валидацию данных
6. Добавьте WebSocket если нужно
7. Напишите тесты
8. Разверните в продакшене

Удачи в разработке с QakeAPI! 🚀
