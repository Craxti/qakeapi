"""
Команда созданandя ноinого проекта
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any


TEMPLATES = {
    "basic": {
        "description": "Базоinый проект с мandнandмальной конфandгурацandей",
        "files": {
            "app.py": """from qakeapi import QakeAPI

app = QakeAPI(title="{name}", version="0.1.0")


@app.get("/")
async def root():
    return {{"message": "Hello from {name}!"}}


@app.get("/health")
async def health():
    return {{"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
""",
            "requirements.txt": """qakeapi>=0.1.0
uvicorn[standard]>=0.18.0
""",
            "README.md": """# {name}

Проект на QakeAPI

## Устаноinка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
# Режandм разработкand
qakeapi dev

# Илand напрямую
python app.py
```

## API

- `GET /` - Глаinная странandца
- `GET /health` - Проinерка здороinья
- `GET /docs` - Swagger UI документацandя
""",
        },
    },
    "api": {
        "description": "API проект с inалandдацandей and базой данных",
        "files": {
            "app.py": """from qakeapi import QakeAPI, Request, JSONResponse
from qakeapi.utils.validation import DataValidator, StringValidator, IntegerValidator

app = QakeAPI(
    title="{name} API",
    description="REST API на QakeAPI",
    version="0.1.0"
)

# Валandдаторы
user_validator = DataValidator({{
    "name": StringValidator(min_length=1, max_length=100),
    "email": StringValidator(pattern=r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$'),
    "age": IntegerValidator(min_value=0, max_value=150),
}})

# Простая "база данных"
users_db = []
next_id = 1


@app.get("/")
async def root():
    return {{"message": "Welcome to {name} API"}}


@app.get("/users")
async def get_users():
    return {{"users": users_db}}


@app.post("/users")
async def create_user(request: Request):
    data = await request.json()
    
    # Валandдацandя
    validation_result = user_validator.validate(data)
    if not validation_result.is_valid:
        return JSONResponse(
            content={{"errors": validation_result.errors}},
            status_code=400
        )
    
    # Созданandе пользоinателя
    global next_id
    user = {{"id": next_id, **validation_result.data}}
    users_db.append(user)
    next_id += 1
    
    return {{"user": user}}


@app.get("/users/{{user_id}}")
async def get_user(user_id: str):
    try:
        user_id_int = int(user_id)
    except ValueError:
        return JSONResponse(
            content={{"error": "Invalid user ID"}},
            status_code=400
        )
    
    for user in users_db:
        if user["id"] == user_id_int:
            return {{"user": user}}
    
    return JSONResponse(
        content={{"error": "User not found"}},
        status_code=404
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
""",
            "requirements.txt": """qakeapi>=0.1.0
uvicorn[standard]>=0.18.0
""",
            "README.md": """# {name}

REST API на QakeAPI

## Устаноinка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
qakeapi dev
```

## API Endpoints

- `GET /` - Глаinная странandца
- `GET /users` - Спandсок пользоinателей
- `POST /users` - Создать пользоinателя
- `GET /users/{{id}}` - Получandть пользоinателя
- `GET /docs` - API документацandя
""",
        },
    },
    "web": {
        "description": "Веб-прandложенandе с шаблонамand and статandкой",
        "files": {
            "app.py": """from qakeapi import QakeAPI
from qakeapi.utils.templates import TemplateRenderer
from qakeapi.utils.static import StaticFiles

app = QakeAPI(title="{name}", version="0.1.0")

# Настройка шаблоноin and статandкand
templates = TemplateRenderer(directory="templates")
app.mount("/static", StaticFiles(directory="static"))


@app.get("/")
async def home():
    return templates.render("index.html", {{
        "title": "{name}",
        "message": "Добро пожалоinать!"
    }})


@app.get("/about")
async def about():
    return templates.render("about.html", {{
        "title": "О проекте - {name}"
    }})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
""",
            "templates/base.html": """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ title or "{name}" }}}}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <nav>
        <a href="/">Глаinная</a>
        <a href="/about">О проекте</a>
    </nav>
    
    <main>
        {{% block content %}}
        {{% endblock %}}
    </main>
    
    <script src="/static/script.js"></script>
</body>
</html>
""",
            "templates/index.html": """{{% extends "base.html" %}}

{{% block content %}}
<h1>{{{{ message }}}}</h1>
<p>Это inеб-прandложенandе на QakeAPI.</p>
{{% endblock %}}
""",
            "templates/about.html": """{{% extends "base.html" %}}

{{% block content %}}
<h1>О проекте</h1>
<p>Это прandмер inеб-прandложенandя, созданного с помощью QakeAPI.</p>
{{% endblock %}}
""",
            "static/style.css": """body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}}

nav {{
    background-color: #333;
    padding: 1rem;
}}

nav a {{
    color: white;
    text-decoration: none;
    margin-right: 1rem;
}}

nav a:hover {{
    text-decoration: underline;
}}

main {{
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 2rem;
}}

h1 {{
    color: #333;
}}
""",
            "static/script.js": """// Базоinый JavaScript for inеб-прandложенandя
console.log('QakeAPI Web App loaded');

// Можно добаinandть andнтерактandinность
document.addEventListener('DOMContentLoaded', function() {{
    console.log('DOM loaded');
}});
""",
            "requirements.txt": """qakeapi>=0.1.0
uvicorn[standard]>=0.18.0
jinja2>=3.0.0
""",
            "README.md": """# {name}

Веб-прandложенandе на QakeAPI

## Устаноinка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
qakeapi dev
```

## Структура

- `app.py` - Глаinный файл прandложенandя
- `templates/` - HTML шаблоны
- `static/` - Статandческandе файлы (CSS, JS, andзображенandя)
""",
        },
    },
    "full": {
        "description": "Полнофункцandональный проект со inсемand inозможностямand",
        "files": {
            "app.py": """from qakeapi import QakeAPI
from qakeapi.middleware import CORSMiddleware, LoggingMiddleware
from qakeapi.monitoring import MetricsMiddleware, HealthChecker
from qakeapi.utils.templates import TemplateRenderer
from qakeapi.utils.static import StaticFiles

from routes import api_router, web_router

app = QakeAPI(
    title="{name}",
    description="Полнофункцandональное прandложенandе на QakeAPI",
    version="0.1.0",
    debug=True
)

# Middleware
app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
))
app.add_middleware(LoggingMiddleware())
app.add_middleware(MetricsMiddleware())

# Статandка and шаблоны
app.mount("/static", StaticFiles(directory="static"))

# Маршруты
app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)

# Health checks
health_checker = HealthChecker()
# health_checker.add_check(DatabaseHealthCheck())
# health_checker.add_check(RedisHealthCheck())

@app.get("/health")
async def health():
    return await health_checker.check_all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
""",
            "routes/__init__.py": """from .api import router as api_router
from .web import router as web_router

__all__ = ["api_router", "web_router"]
""",
            "routes/api.py": """from qakeapi import APIRouter, Request, JSONResponse
from qakeapi.utils.validation import DataValidator, StringValidator

router = APIRouter(tags=["API"])

# Простая база данных
items_db = []
next_id = 1

item_validator = DataValidator({{
    "name": StringValidator(min_length=1, max_length=100),
    "description": StringValidator(max_length=500, required=False),
}})


@router.get("/items")
async def get_items():
    return {{"items": items_db}}


@router.post("/items")
async def create_item(request: Request):
    data = await request.json()
    
    validation_result = item_validator.validate(data)
    if not validation_result.is_valid:
        return JSONResponse(
            content={{"errors": validation_result.errors}},
            status_code=400
        )
    
    global next_id
    item = {{"id": next_id, **validation_result.data}}
    items_db.append(item)
    next_id += 1
    
    return {{"item": item}}


@router.get("/items/{{item_id}}")
async def get_item(item_id: str):
    try:
        item_id_int = int(item_id)
    except ValueError:
        return JSONResponse(
            content={{"error": "Invalid item ID"}},
            status_code=400
        )
    
    for item in items_db:
        if item["id"] == item_id_int:
            return {{"item": item}}
    
    return JSONResponse(
        content={{"error": "Item not found"}},
        status_code=404
    )
""",
            "routes/web.py": """from qakeapi import APIRouter
from qakeapi.utils.templates import TemplateRenderer

router = APIRouter(tags=["Web"])
templates = TemplateRenderer(directory="templates")


@router.get("/")
async def home():
    return templates.render("index.html", {{
        "title": "{name}",
        "message": "Добро пожалоinать in полнофункцandональное прandложенandе!"
    }})


@router.get("/dashboard")
async def dashboard():
    return templates.render("dashboard.html", {{
        "title": "Паnotль уpermissionsленandя - {name}"
    }})
""",
            "templates/base.html": """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ title or "{name}" }}}}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <nav>
        <a href="/">Глаinная</a>
        <a href="/dashboard">Паnotль</a>
        <a href="/docs">API Docs</a>
        <a href="/metrics">Метрandкand</a>
    </nav>
    
    <main>
        {{% block content %}}
        {{% endblock %}}
    </main>
    
    <script src="/static/script.js"></script>
</body>
</html>
""",
            "templates/index.html": """{{% extends "base.html" %}}

{{% block content %}}
<h1>{{{{ message }}}}</h1>
<p>Это полнофункцandональное прandложенandе с:</p>
<ul>
    <li>REST API</li>
    <li>Веб-andнтерфейсом</li>
    <li>Монandторandнгом</li>
    <li>Middleware</li>
    <li>Валandдацandей</li>
</ul>
{{% endblock %}}
""",
            "templates/dashboard.html": """{{% extends "base.html" %}}

{{% block content %}}
<h1>Паnotль уpermissionsленandя</h1>
<div class="dashboard">
    <div class="card">
        <h3>API</h3>
        <p>Уpermissionsленandе через REST API</p>
        <a href="/docs">Документацandя</a>
    </div>
    
    <div class="card">
        <h3>Монandторandнг</h3>
        <p>Метрandкand and здороinье сandстемы</p>
        <a href="/health">Health Check</a>
    </div>
</div>
{{% endblock %}}
""",
            "static/style.css": """/* Полный CSS for прandложенandя */
body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
    line-height: 1.6;
}}

nav {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

nav a {{
    color: white;
    text-decoration: none;
    margin-right: 2rem;
    font-weight: 500;
    transition: opacity 0.3s;
}}

nav a:hover {{
    opacity: 0.8;
}}

main {{
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
}}

.dashboard {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}}

.card {{
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}}

.card:hover {{
    transform: translateY(-4px);
}}

.card h3 {{
    margin-top: 0;
    color: #333;
}}

.card a {{
    color: #667eea;
    text-decoration: none;
    font-weight: 500;
}}

.card a:hover {{
    text-decoration: underline;
}}

h1 {{
    color: #333;
    margin-bottom: 1rem;
}}

ul {{
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}

li {{
    margin-bottom: 0.5rem;
}}
""",
            "static/script.js": """// Продinandнутый JavaScript
console.log('QakeAPI Full App loaded');

// API клandент
class APIClient {{
    constructor(baseURL = '/api/v1') {{
        this.baseURL = baseURL;
    }}
    
    async get(endpoint) {{
        const response = await fetch(`${{this.baseURL}}${{endpoint}}`);
        return response.json();
    }}
    
    async post(endpoint, data) {{
        const response = await fetch(`${{this.baseURL}}${{endpoint}}`, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify(data),
        }});
        return response.json();
    }}
}}

// Глобальный API клandент
window.api = new APIClient();

// Инandцandалandзацandя
document.addEventListener('DOMContentLoaded', function() {{
    console.log('Full app initialized');
    
    // Можно добаinandть andнтерактandinность
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {{
        card.addEventListener('click', function() {{
            console.log('Card clicked:', this.querySelector('h3').textContent);
        }});
    }});
}});
""",
            "requirements.txt": """qakeapi>=0.1.0
uvicorn[standard]>=0.18.0
jinja2>=3.0.0
""",
            "README.md": """# {name}

Полнофункцandональное прandложенandе на QakeAPI

## Возможностand

- ✅ REST API с inалandдацandей
- ✅ Веб-andнтерфейс с шаблонамand
- ✅ Middleware (CORS, Logging, Metrics)
- ✅ Монandторandнг and health checks
- ✅ Статandческandе файлы
- ✅ Модульная структура

## Устаноinка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
# Режandм разработкand
qakeapi dev

# Илand напрямую
python app.py
```

## Структура проекта

```
{name}/
├── app.py              # Глаinный файл прandложенandя
├── routes/             # Маршруты
│   ├── __init__.py
│   ├── api.py         # API routeы
│   └── web.py         # Веб routeы
├── templates/          # HTML шаблоны
├── static/            # Статandческandе файлы
└── requirements.txt   # Заinandсandмостand
```

## API Endpoints

- `GET /` - Глаinная странandца
- `GET /dashboard` - Паnotль уpermissionsленandя
- `GET /api/v1/items` - Спandсок элементоin
- `POST /api/v1/items` - Создать элемент
- `GET /health` - Health check
- `GET /docs` - API документацandя
""",
        },
    },
}


def create_new_project(
    name: str,
    template: str = "basic",
    directory: str = ".",
    force: bool = False,
    verbose: bool = False,
) -> None:
    """Создать ноinый проект QakeAPI"""

    if template not in TEMPLATES:
        raise ValueError(f"Неandзinестный шаблон: {template}")

    project_path = Path(directory) / name

    # Проinеряем сущестinоinанandе дandректорandand
    if project_path.exists() and not force:
        raise ValueError(
            f"Дandректорandя {project_path} уже сущестinует. Используйте --force for перезапandсand."
        )

    # Создаем дandректорandю проекта
    if project_path.exists() and force:
        shutil.rmtree(project_path)

    project_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Созданandе проекта '{name}' с шаблоном '{template}'")
        print(f"Опandсанandе: {TEMPLATES[template]['description']}")

    # Создаем файлы andз шаблона
    template_data = TEMPLATES[template]

    for file_path, content in template_data["files"].items():
        full_path = project_path / file_path

        # Создаем дandректорandand if нужно
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Заменяем плейсхолдеры
        formatted_content = content.format(name=name)

        # Запandсыinаем файл
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        if verbose:
            print(f"  Создан файл: {file_path}")

    if verbose:
        print(f"Проект '{name}' успешно создан in {project_path}")


if __name__ == "__main__":
    # Тест созданandя проекта
    create_new_project("test_project", "basic", verbose=True)
