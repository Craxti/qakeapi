# -*- coding: utf-8 -*-
"""
Базовый пример использования QakeAPI.
"""
from __future__ import annotations
import asyncio
from typing import Dict, List, Optional
from qakeapi import Application
from qakeapi.security.auth import SecurityUtils, require_auth, rate_limit
from qakeapi.validation.validators import CreateUser, UpdateUser, PaginationParams
from qakeapi.core.logging import setup_logging, RequestLogger
import json

# Настройка логирования
logger = setup_logging(level="DEBUG", json_output=True)
request_logger = RequestLogger(logger)

# Инициализация приложения
app = Application()

# Имитация базы данных
users_db = {}

async def root(request):
    """Базовый эндпоинт для проверки работоспособности."""
    return {"status": "online"}

@rate_limit(limit=10, window=60)  # 10 запросов в минуту
@app.route("/users", methods=["POST"])
async def create_user(request):
    """Создание нового пользователя."""
    try:
        user_data = await request.json()
        if not isinstance(user_data, dict):
            return {"error": "Invalid JSON data"}, 400
            
        # Валидация данных
        if not all(key in user_data for key in ["username", "email", "password"]):
            return {"error": "Missing required fields"}, 400
            
        # Проверка на существующего пользователя
        if user_data["username"] in users_db:
            return {"error": "User already exists"}, 400
            
        # Хеширование пароля
        hashed_password = SecurityUtils.get_password_hash(user_data["password"])
        
        # Сохранение пользователя
        user_data["password"] = hashed_password
        users_db[user_data["username"]] = user_data
        
        return {"message": "User created", "username": user_data["username"]}
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return {"error": str(e)}, 400

@require_auth()
async def get_user(request):
    """Получение информации о пользователе."""
    username = request.path_params['username']
    if username not in users_db:
        return {"error": "User not found"}, 404
    
    user_data = users_db[username].copy()
    del user_data["password"]  # Не возвращаем хеш пароля
    return user_data

@require_auth()
async def update_user(request):
    """Обновление информации о пользователе."""
    username = request.path_params['username']
    if username not in users_db:
        return {"error": "User not found"}, 404
    
    # Обновление данных
    user_data = await request.json()
    user_data = UpdateUser(**user_data)
    stored_user = users_db[username]
    update_data = user_data.dict(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password"] = SecurityUtils.get_password_hash(update_data["password"])
    
    stored_user.update(update_data)
    return {"message": "User updated"}

@require_auth(scopes=["admin"])
async def delete_user(request):
    """Удаление пользователя (только для админов)."""
    username = request.path_params['username']
    if username not in users_db:
        return {"error": "User not found"}, 404
    
    del users_db[username]
    return {"message": "User deleted"}

@require_auth()
async def list_users(request):
    """Получение списка пользователей с пагинацией."""
    # Получение параметров пагинации из query string
    params = PaginationParams(
        page=request.query_params.get('page', '1'),
        per_page=request.query_params.get('per_page', '10')
    )
    
    # Получение списка пользователей без паролей
    users_list = []
    for username, user_data in users_db.items():
        user_copy = user_data.copy()
        del user_copy["password"]
        users_list.append(user_copy)
    
    # Пагинация
    start = (params.page - 1) * params.per_page
    end = start + params.per_page
    
    return {
        "total": len(users_list),
        "page": params.page,
        "per_page": params.per_page,
        "users": users_list[start:end]
    }

# Регистрация всех маршрутов
app.router.routes = []  # Очистка существующих маршрутов

# Регистрация маршрутов в правильном порядке
app.router.add_route("/", root, ["GET"])
app.router.add_route("/users", list_users, ["GET"])
app.router.add_route("/users", create_user, ["POST"])

# Регистрация маршрутов с параметрами
app.router.add_route("/users/{username}", get_user, ["GET"])
app.router.add_route("/users/{username}", update_user, ["PUT"])
app.router.add_route("/users/{username}", delete_user, ["DELETE"])

# Обновление методов для каждого маршрута
for route in app.router.routes:
    if route.path == "/users/{username}":
        route.methods = ["GET", "PUT", "DELETE"]
    elif route.path == "/users":
        route.methods = ["GET", "POST"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
