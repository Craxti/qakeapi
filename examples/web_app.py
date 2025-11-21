"""
Пример веб-приложения с шаблонами и статическими файлами
"""

import os

from qakeapi import QakeAPI, Request
from qakeapi.core.responses import HTMLResponse, RedirectResponse
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.utils.static import mount_static
from qakeapi.utils.templates import Jinja2Templates, SimpleTemplates

# Создаем приложение
app = QakeAPI(
    title="QakeAPI Веб-приложение",
    description="Пример веб-приложения с шаблонами и статическими файлами",
    version="1.0.0",
    debug=True,
)

# Добавляем CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Создаем директории для шаблонов и статических файлов
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Создаем базовые шаблоны
base_template = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - QakeAPI App</title>
    <link rel="stylesheet" href="/static/style.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
            border-radius: 10px;
        }}
        .nav {{
            background: white;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .nav a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 1rem;
            font-weight: 500;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
        .card {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }}
        .btn {{
            background: #667eea;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }}
        .btn:hover {{
            background: #5a6fd8;
        }}
        .form-group {{
            margin-bottom: 1rem;
        }}
        .form-group label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}
        .form-group input, .form-group textarea {{
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }}
        .alert {{
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }}
        .alert-success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .alert-error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🚀 QakeAPI Веб-приложение</h1>
            <p>Демонстрация возможностей фреймворка</p>
        </header>
        
        <nav class="nav">
            <a href="/">Главная</a>
            <a href="/about">О нас</a>
            <a href="/contact">Контакты</a>
            <a href="/users">Пользователи</a>
            <a href="/docs">API Документация</a>
        </nav>
        
        <main>
            {content}
        </main>
    </div>
    <script src="/static/script.js"></script>
</body>
</html>"""

index_template = """<div class="card">
    <h2>Добро пожаловать!</h2>
    <p>Это пример веб-приложения, созданного с помощью <strong>QakeAPI</strong> - мощного асинхронного веб-фреймворка для Python.</p>
    
    <h3>Возможности фреймворка:</h3>
    <ul>
        <li>🚀 Асинхронная обработка запросов</li>
        <li>🔒 Встроенная система аутентификации</li>
        <li>🌐 CORS и другие middleware</li>
        <li>📝 Автоматическая валидация данных</li>
        <li>🔌 WebSocket поддержка</li>
        <li>📚 Автоматическая генерация документации</li>
        <li>🎨 Поддержка шаблонов и статических файлов</li>
    </ul>
    
    <p>
        <a href="/about" class="btn">Узнать больше</a>
        <a href="/users" class="btn">Посмотреть пользователей</a>
    </p>
</div>

<div class="card">
    <h3>Быстрый старт</h3>
    <p>Создайте свое первое приложение:</p>
    <pre style="background: #f8f9fa; padding: 1rem; border-radius: 4px; overflow-x: auto;"><code>from qakeapi import QakeAPI

app = QakeAPI(title="Мое приложение")

@app.get("/")
async def root():
    return {{"message": "Привет, мир!"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)</code></pre>
</div>"""

about_template = """<div class="card">
    <h2>О QakeAPI</h2>
    <p><strong>QakeAPI</strong> - это современный, быстрый веб-фреймворк для создания API на Python, основанный на стандартных подсказках типов Python 3.8+.</p>
    
    <h3>Ключевые особенности:</h3>
    <ul>
        <li><strong>Быстрый:</strong> Очень высокая производительность, сравнимая с NodeJS и Go</li>
        <li><strong>Быстрый в разработке:</strong> Увеличение скорости разработки на 200-300%</li>
        <li><strong>Меньше багов:</strong> Сокращение количества ошибок на 40%</li>
        <li><strong>Интуитивный:</strong> Отличная поддержка редактора с автодополнением</li>
        <li><strong>Простой:</strong> Разработан для простоты использования и изучения</li>
        <li><strong>Короткий:</strong> Минимизация дублирования кода</li>
        <li><strong>Надежный:</strong> Получите готовый к продакшену код с автоматической интерактивной документацией</li>
        <li><strong>Основан на стандартах:</strong> Основан на открытых стандартах для API: OpenAPI и JSON Schema</li>
    </ul>
</div>

<div class="card">
    <h3>Архитектура</h3>
    <p>QakeAPI построен на следующих принципах:</p>
    <ul>
        <li><strong>ASGI:</strong> Асинхронный интерфейс шлюза сервера</li>
        <li><strong>Pydantic:</strong> Валидация данных с использованием подсказок типов Python</li>
        <li><strong>Starlette:</strong> Легкий ASGI фреймворк/toolkit</li>
        <li><strong>OpenAPI:</strong> Автоматическая генерация документации API</li>
    </ul>
</div>"""

contact_template = """<div class="card">
    <h2>Свяжитесь с нами</h2>
    <p>Есть вопросы или предложения? Мы будем рады услышать от вас!</p>
    
    {message}
    
    <form method="post" action="/contact">
        <div class="form-group">
            <label for="name">Имя:</label>
            <input type="text" id="name" name="name" required>
        </div>
        
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>
        </div>
        
        <div class="form-group">
            <label for="subject">Тема:</label>
            <input type="text" id="subject" name="subject" required>
        </div>
        
        <div class="form-group">
            <label for="message">Сообщение:</label>
            <textarea id="message" name="message" rows="5" required></textarea>
        </div>
        
        <button type="submit" class="btn">Отправить сообщение</button>
    </form>
</div>

<div class="card">
    <h3>Другие способы связи</h3>
    <ul>
        <li>📧 Email: support@qakeapi.dev</li>
        <li>🐙 GitHub: https://github.com/qakeapi/qakeapi</li>
        <li>📚 Документация: https://qakeapi.dev/docs</li>
        <li>💬 Сообщество: https://discord.gg/qakeapi</li>
    </ul>
</div>"""

users_template = """<div class="card">
    <h2>Пользователи системы</h2>
    <p>Список зарегистрированных пользователей:</p>
    
    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #dee2e6;">ID</th>
                    <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #dee2e6;">Имя</th>
                    <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #dee2e6;">Email</th>
                    <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid #dee2e6;">Статус</th>
                </tr>
            </thead>
            <tbody>
                {users_rows}
            </tbody>
        </table>
    </div>
    
    <p style="margin-top: 1rem;">
        <a href="/users/new" class="btn">Добавить пользователя</a>
    </p>
</div>"""

# Записываем шаблоны в файлы
with open("templates/base.html", "w", encoding="utf-8") as f:
    f.write(base_template)

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(index_template)

with open("templates/about.html", "w", encoding="utf-8") as f:
    f.write(about_template)

with open("templates/contact.html", "w", encoding="utf-8") as f:
    f.write(contact_template)

with open("templates/users.html", "w", encoding="utf-8") as f:
    f.write(users_template)

# Создаем CSS файл
css_content = """/* Дополнительные стили */
.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}"""

with open("static/style.css", "w", encoding="utf-8") as f:
    f.write(css_content)

# Создаем JS файл
js_content = """// Простые интерактивные функции
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем анимацию появления для карточек
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Обработка форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="loading"></span> Отправка...';
                submitBtn.disabled = true;
            }
        });
    });
    
    console.log('🚀 QakeAPI Web App загружено!');
});"""

with open("static/script.js", "w", encoding="utf-8") as f:
    f.write(js_content)

# Инициализируем шаблоны
try:
    templates = Jinja2Templates(directory="templates")
except:
    # Если Jinja2 не установлена, используем простые шаблоны
    templates = SimpleTemplates(directory="templates")

# Подключаем статические файлы
mount_static(app, "/static", directory="static", name="static")

# Фиктивная база данных пользователей
fake_users = [
    {"id": 1, "name": "Алиса Иванова", "email": "alice@example.com", "active": True},
    {"id": 2, "name": "Боб Петров", "email": "bob@example.com", "active": True},
    {"id": 3, "name": "Кэрол Сидорова", "email": "carol@example.com", "active": False},
    {"id": 4, "name": "Дэвид Козлов", "email": "david@example.com", "active": True},
]


# Маршруты
@app.get("/")
async def home():
    """Главная страница"""
    content = templates.render("index.html", {})
    return HTMLResponse(
        templates.render("base.html", {"title": "Главная", "content": content})
    )


@app.get("/about")
async def about():
    """Страница о нас"""
    content = templates.render("about.html", {})
    return HTMLResponse(
        templates.render("base.html", {"title": "О нас", "content": content})
    )


@app.get("/contact")
async def contact_get():
    """Страница контактов (GET)"""
    content = templates.render("contact.html", {"message": ""})
    return HTMLResponse(
        templates.render("base.html", {"title": "Контакты", "content": content})
    )


@app.post("/contact")
async def contact_post(request: Request):
    """Обработка формы контактов (POST)"""
    form_data = await request.form()

    # Здесь можно добавить логику отправки email
    print(f"Получено сообщение от {form_data.get('name')} ({form_data.get('email')})")
    print(f"Тема: {form_data.get('subject')}")
    print(f"Сообщение: {form_data.get('message')}")

    message = '<div class="alert alert-success">Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.</div>'
    content = templates.render("contact.html", {"message": message})

    return HTMLResponse(
        templates.render("base.html", {"title": "Контакты", "content": content})
    )


@app.get("/users")
async def users_list():
    """Список пользователей"""
    users_rows = ""
    for user in fake_users:
        status = "Активен" if user["active"] else "Неактивен"
        status_color = "#28a745" if user["active"] else "#dc3545"
        users_rows += f"""
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid #dee2e6;">{user['id']}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #dee2e6;">{user['name']}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #dee2e6;">{user['email']}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #dee2e6; color: {status_color};">{status}</td>
        </tr>
        """

    content = templates.render("users.html", {"users_rows": users_rows})
    return HTMLResponse(
        templates.render("base.html", {"title": "Пользователи", "content": content})
    )


@app.get("/users/new")
async def new_user_form():
    """Форма добавления пользователя"""
    form_html = """
    <div class="card">
        <h2>Добавить пользователя</h2>
        <form method="post" action="/users/new">
            <div class="form-group">
                <label for="name">Имя:</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" name="active" value="1" checked> Активный пользователь
                </label>
            </div>
            
            <button type="submit" class="btn">Добавить пользователя</button>
            <a href="/users" class="btn" style="background: #6c757d; margin-left: 0.5rem;">Отмена</a>
        </form>
    </div>
    """

    return HTMLResponse(
        templates.render(
            "base.html", {"title": "Новый пользователь", "content": form_html}
        )
    )


@app.post("/users/new")
async def create_user(request: Request):
    """Создание нового пользователя"""
    form_data = await request.form()

    new_user = {
        "id": len(fake_users) + 1,
        "name": form_data.get("name"),
        "email": form_data.get("email"),
        "active": bool(form_data.get("active")),
    }

    fake_users.append(new_user)

    return RedirectResponse(url="/users", status_code=303)


# API маршруты для AJAX
@app.get("/api/users")
async def api_users():
    """API для получения пользователей"""
    return {"users": fake_users}


@app.post("/api/users")
async def api_create_user(request: Request):
    """API для создания пользователя"""
    data = await request.json()

    new_user = {
        "id": len(fake_users) + 1,
        "name": data.get("name"),
        "email": data.get("email"),
        "active": data.get("active", True),
    }

    fake_users.append(new_user)

    return {"message": "Пользователь создан", "user": new_user}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Запуск QakeAPI веб-приложения...")
    print("📂 Статические файлы: /static/")
    print("🎨 Шаблоны: templates/")
    print("🌐 Приложение доступно по адресу: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
