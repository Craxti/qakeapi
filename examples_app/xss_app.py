# -*- coding: utf-8 -*-
"""
Пример XSS защиты с QakeAPI.
"""
import sys
import os
import html
import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote, unquote

# Добавляем путь к локальному QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.core.middleware import Middleware
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import BaseModel, Field, validator

# Инициализация приложения
app = Application(title="XSS Protection Example", version="1.0.0")

# Pydantic модели с валидацией XSS
class CommentRequest(RequestModel):
    """Модель для комментария с XSS защитой"""
    author: str = Field(..., min_length=1, max_length=100, description="Автор комментария")
    content: str = Field(..., min_length=1, max_length=1000, description="Содержание комментария")
    email: Optional[str] = Field(None, description="Email автора")
    website: Optional[str] = Field(None, description="Веб-сайт автора")
    
    @validator('author')
    def validate_author(cls, v):
        """Валидация имени автора"""
        if not v or not v.strip():
            raise ValueError('Author name cannot be empty')
        
        # Проверяем на опасные символы
        dangerous_chars = ['<', '>', '"', "'", '&', 'javascript:', 'onload', 'onerror']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'Author name contains dangerous characters: {char}')
        
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Валидация содержания комментария"""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        
        # Проверяем на HTML теги
        if re.search(r'<[^>]+>', v):
            raise ValueError('Content cannot contain HTML tags')
        
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        """Валидация email"""
        if v is None:
            return v
        
        # Простая проверка email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        return v.lower()
    
    @validator('website')
    def validate_website(cls, v):
        """Валидация веб-сайта"""
        if v is None:
            return v
        
        # Проверяем протокол
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        # Простая проверка URL
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid website URL')
        
        return v

class MessageRequest(RequestModel):
    """Модель для сообщения"""
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок сообщения")
    message: str = Field(..., min_length=1, max_length=5000, description="Текст сообщения")
    recipient: str = Field(..., description="Получатель")

class SearchRequest(RequestModel):
    """Модель для поиска"""
    query: str = Field(..., min_length=1, max_length=100, description="Поисковый запрос")
    category: Optional[str] = Field(None, description="Категория")

# Имитация базы данных
comments_db = []
messages_db = []
search_history = []

# Эндпоинты

@app.get("/")
async def root(request: Request):
    """Базовый эндпоинт"""
    return {
        "message": "XSS Protection Example API is running",
        "endpoints": {
            "/comments": "GET/POST - Управление комментариями",
            "/messages": "POST - Отправка сообщений",
            "/search": "POST - Поиск с защитой",
            "/preview": "POST - Предварительный просмотр",
            "/sanitize": "POST - Очистка текста",
            "/test-xss": "GET - Тестовые XSS векторы"
        },
        "security_features": [
            "Автоматическая очистка HTML",
            "Валидация входных данных",
            "Защита от XSS атак",
            "Content Security Policy",
            "Безопасные заголовки"
        ]
    }

@app.get("/comments")
async def get_comments(request: Request):
    """Получить список комментариев"""
    return {
        "comments": comments_db,
        "total_count": len(comments_db)
    }

@app.post("/comments")
@validate_request_body(CommentRequest)
async def create_comment(request: Request):
    """
    Создать комментарий с XSS защитой
    
    Этот эндпоинт демонстрирует защиту от XSS атак:
    1. Валидация входных данных
    2. Очистка HTML
    3. Безопасное отображение
    """
    data = request.validated_data
    
    # Дополнительная очистка данных
    sanitized_comment = {
        "id": len(comments_db) + 1,
        "author": html.escape(data.author),
        "content": html.escape(data.content),
        "email": html.escape(data.email) if data.email else None,
        "website": data.website,  # URL уже проверен
        "created_at": datetime.utcnow().isoformat(),
        "sanitized": True
    }
    
    comments_db.append(sanitized_comment)
    
    return {
        "message": "Comment created successfully",
        "comment": sanitized_comment
    }

@app.post("/messages")
@validate_request_body(MessageRequest)
async def send_message(request: Request):
    """
    Отправить сообщение с XSS защитой
    """
    data = request.validated_data
    
    # Очищаем данные
    sanitized_message = {
        "id": len(messages_db) + 1,
        "title": html.escape(data.title),
        "message": html.escape(data.message),
        "recipient": html.escape(data.recipient),
        "created_at": datetime.utcnow().isoformat()
    }
    
    messages_db.append(sanitized_message)
    
    return {
        "message": "Message sent successfully",
        "message_data": sanitized_message
    }

@app.post("/search")
@validate_request_body(SearchRequest)
async def search_content(request: Request):
    """
    Поиск с XSS защитой
    """
    data = request.validated_data
    
    # Очищаем поисковый запрос
    sanitized_query = html.escape(data.query)
    
    # Имитируем поиск
    search_results = [
        {
            "id": 1,
            "title": f"Result for: {sanitized_query}",
            "content": f"This is a search result for '{sanitized_query}'",
            "url": f"https://example.com/search?q={quote(sanitized_query)}"
        }
    ]
    
    # Сохраняем в историю
    search_history.append({
        "query": sanitized_query,
        "category": html.escape(data.category) if data.category else None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "query": sanitized_query,
        "results": search_results,
        "total_results": len(search_results)
    }

@app.post("/preview")
async def preview_content(request: Request):
    """
    Предварительный просмотр с XSS защитой
    """
    try:
        body = await request.json()
        content = body.get("content", "")
        
        # Очищаем контент
        sanitized_content = html.escape(content)
        
        return {
            "original": content,
            "sanitized": sanitized_content,
            "preview": f"<div class='preview'>{sanitized_content}</div>"
        }
    except Exception as e:
        return Response.json(
            {"error": "Invalid JSON data", "details": str(e)},
            status_code=400
        )

@app.post("/sanitize")
async def sanitize_text(request: Request):
    """
    Очистка текста от потенциально опасного содержимого
    """
    try:
        body = await request.json()
        text = body.get("text", "")
        
        # Получаем middleware
        xss_middleware = None
        for middleware in app.http_router._middleware:
            if hasattr(middleware, '__name__') and middleware.__name__ == "XSSProtectionMiddleware":
                xss_middleware = middleware
                break
        
        if not xss_middleware:
            return Response.json(
                {"error": "XSS middleware not found"},
                status_code=500
            )
        
        # Очищаем текст
        sanitized_text = xss_middleware.sanitize_html(text)
        
        return {
            "original": text,
            "sanitized": sanitized_text,
            "has_dangerous_content": text != sanitized_text
        }
    except Exception as e:
        return Response.json(
            {"error": "Invalid JSON data", "details": str(e)},
            status_code=400
        )

@app.get("/test-xss")
async def test_xss_vectors(request: Request):
    """
    Тестовые XSS векторы для демонстрации защиты
    """
    test_vectors = [
        {
            "name": "Basic Script Tag",
            "vector": "<script>alert('XSS')</script>",
            "description": "Базовый тег script"
        },
        {
            "name": "JavaScript Protocol",
            "vector": "javascript:alert('XSS')",
            "description": "JavaScript протокол в URL"
        },
        {
            "name": "Event Handler",
            "vector": "<img src=x onerror=alert('XSS')>",
            "description": "Обработчик события onerror"
        },
        {
            "name": "Iframe Injection",
            "vector": "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "description": "Внедрение iframe"
        },
        {
            "name": "CSS Injection",
            "vector": "<div style='background:url(javascript:alert(\"XSS\"))'>",
            "description": "CSS injection"
        },
        {
            "name": "HTML Entity Encoding",
            "vector": "&lt;script&gt;alert('XSS')&lt;/script&gt;",
            "description": "HTML entities"
        },
        {
            "name": "Unicode Encoding",
            "vector": "\\u003Cscript\\u003Ealert('XSS')\\u003C/script\\u003E",
            "description": "Unicode encoding"
        },
        {
            "name": "Mixed Case",
            "vector": "<ScRiPt>alert('XSS')</ScRiPt>",
            "description": "Смешанный регистр"
        },
        {
            "name": "Nested Tags",
            "vector": "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
            "description": "Вложенные теги"
        },
        {
            "name": "Null Byte",
            "vector": "<script>alert('XSS')</script>",
            "description": "Null byte injection"
        }
    ]
    
    return {
        "message": "XSS Test Vectors",
        "description": "Эти векторы используются для тестирования XSS защиты",
        "vectors": test_vectors,
        "warning": "Не используйте эти векторы в продакшене!"
    }

@app.get("/search-history")
async def get_search_history(request: Request):
    """Получить историю поиска"""
    return {
        "search_history": search_history[-10:],  # Последние 10 запросов
        "total_searches": len(search_history)
    }

@app.get("/security-headers")
async def get_security_headers(request: Request):
    """Получить информацию о заголовках безопасности"""
    return {
        "message": "Security Headers Information",
        "headers": {
            "X-XSS-Protection": "1; mode=block",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        },
        "description": "Эти заголовки добавляются автоматически middleware"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8015) 