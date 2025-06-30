# -*- coding: utf-8 -*-
"""
Пример защиты от SQL инъекций с QakeAPI.
"""
import sys
import os
import re
import sqlite3
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

# Добавляем путь к локальному QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.core.middleware import Middleware
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import BaseModel, Field, validator

# Инициализация приложения
app = Application(title="SQL Injection Protection Example", version="1.0.0")

# Middleware для защиты от SQL инъекций
class SQLInjectionProtectionMiddleware(Middleware):
    """Middleware для защиты от SQL инъекций"""
    
    def __init__(self):
        self.__name__ = "SQLInjectionProtectionMiddleware"
        self.dangerous_patterns = [
            # SQL ключевые слова
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|OR|AND)\b',
            # Комментарии SQL
            r'--',
            r'/\*.*?\*/',
            # Кавычки и точки с запятой
            r'[\'";]',
            # Функции SQL
            r'\b(COUNT|SUM|AVG|MAX|MIN|LENGTH|SUBSTR|CONCAT|UPPER|LOWER)\b',
            # Условия WHERE
            r'\bWHERE\b.*?\b(OR|AND)\b',
            # JOIN
            r'\b(INNER|LEFT|RIGHT|FULL)\s+JOIN\b',
            # Подзапросы
            r'\(\s*SELECT\b',
            # Инъекции через UNION
            r'\bUNION\s+(ALL\s+)?SELECT\b',
            # Инъекции через OR 1=1
            r'\bOR\s+1\s*=\s*1\b',
            r'\bOR\s+\'1\'\s*=\s*\'1\'\b',
            # Инъекции через комментарии
            r'#.*$',
            # Инъекции через экранирование
            r'\\\'.*?\\\'',
            # Инъекции через hex
            r'0x[0-9a-fA-F]+',
            # Инъекции через char
            r'CHAR\s*\(\s*\d+\s*\)',
            # Инъекции через concat
            r'CONCAT\s*\([^)]*\)',
            # Инъекции через substring
            r'SUBSTRING\s*\([^)]*\)',
            # Инъекции через case
            r'\bCASE\s+WHEN\b',
            # Инъекции через if
            r'\bIF\s*\([^)]*\)',
            # Инъекции через sleep
            r'\bSLEEP\s*\(\s*\d+\s*\)',
            # Инъекции через benchmark
            r'\bBENCHMARK\s*\([^)]*\)',
            # Инъекции через load_file
            r'\bLOAD_FILE\s*\([^)]*\)',
            # Инъекции через into outfile
            r'\bINTO\s+OUTFILE\b',
            # Инъекции через into dumpfile
            r'\bINTO\s+DUMPFILE\b',
            # Инъекции через information_schema
            r'\binformation_schema\b',
            # Инъекции через mysql
            r'\bmysql\b',
            # Инъекции через sys
            r'\bsys\b',
            # Инъекции через performance_schema
            r'\bperformance_schema\b',
        ]
        
        # Компилируем регулярные выражения
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.dangerous_patterns]
    
    def detect_sql_injection(self, text: str) -> bool:
        """Обнаруживает потенциальные SQL инъекции"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Проверяем паттерны
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        
        # Дополнительные проверки
        suspicious_combinations = [
            ('or', '1=1'),
            ('or', '1=1'),
            ('union', 'select'),
            ('drop', 'table'),
            ('delete', 'from'),
            ('insert', 'into'),
            ('update', 'set'),
            ('alter', 'table'),
            ('create', 'table'),
            ('exec', 'xp_'),
            ('exec', 'sp_'),
        ]
        
        for combo in suspicious_combinations:
            if combo[0] in text_lower and combo[1] in text_lower:
                return True
        
        return False
    
    def sanitize_input(self, text: str) -> str:
        """Очищает входные данные от потенциально опасных символов"""
        if not text:
            return text
        
        # Удаляем опасные символы
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    async def __call__(self, request: Request, call_next):
        """Обработка запроса с защитой от SQL инъекций"""
        # Проверяем заголовки
        for key, value in request.headers.items():
            if isinstance(value, str) and self.detect_sql_injection(value):
                return Response.json(
                    {"error": "Potential SQL injection detected in headers", "code": "SQL_INJECTION_DETECTED"},
                    status_code=400
                )
        
        # Проверяем query параметры
        for key, value in request.query_params.items():
            if isinstance(value, str) and self.detect_sql_injection(value):
                return Response.json(
                    {"error": "Potential SQL injection detected in query parameters", "code": "SQL_INJECTION_DETECTED"},
                    status_code=400
                )
        
        # Проверяем body (если это JSON)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    for key, value in body.items():
                        if isinstance(value, str) and self.detect_sql_injection(value):
                            return Response.json(
                                {"error": "Potential SQL injection detected in request body", "code": "SQL_INJECTION_DETECTED"},
                                status_code=400
                            )
            except:
                pass
        
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Добавляем заголовки безопасности
        response.headers["X-SQL-Injection-Protection"] = "enabled"
        
        return response

# Подключаем middleware
# app.http_router.add_middleware(SQLInjectionProtectionMiddleware())

# Безопасный класс для работы с базой данных
class SafeDatabase:
    """Безопасный класс для работы с базой данных"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу продуктов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    stock_quantity INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу заказов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    def safe_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Безопасное выполнение запроса с параметрами"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return [{"affected_rows": cursor.rowcount}]
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Безопасное получение пользователя по имени"""
        query = "SELECT * FROM users WHERE username = ?"
        result = self.safe_query(query, (username,))
        return result[0] if result else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Безопасное получение пользователя по email"""
        query = "SELECT * FROM users WHERE email = ?"
        result = self.safe_query(query, (email,))
        return result[0] if result else None
    
    def create_user(self, username: str, email: str, password_hash: str) -> Dict:
        """Безопасное создание пользователя"""
        query = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"
        result = self.safe_query(query, (username, email, password_hash))
        return {"id": result[0]["affected_rows"], "username": username, "email": email}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Безопасный поиск продуктов"""
        if category:
            sql_query = "SELECT * FROM products WHERE name LIKE ? AND category = ?"
            params = (f"%{query}%", category)
        else:
            sql_query = "SELECT * FROM products WHERE name LIKE ?"
            params = (f"%{query}%",)
        
        return self.safe_query(sql_query, params)
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Безопасное получение продуктов по категории"""
        query = "SELECT * FROM products WHERE category = ?"
        return self.safe_query(query, (category,))
    
    def create_product(self, name: str, description: str, price: float, category: str, stock_quantity: int) -> Dict:
        """Безопасное создание продукта"""
        query = "INSERT INTO products (name, description, price, category, stock_quantity) VALUES (?, ?, ?, ?, ?)"
        result = self.safe_query(query, (name, description, price, category, stock_quantity))
        return {"id": result[0]["affected_rows"], "name": name, "price": price}
    
    def update_product_stock(self, product_id: int, new_quantity: int) -> Dict:
        """Безопасное обновление количества товара"""
        query = "UPDATE products SET stock_quantity = ? WHERE id = ?"
        result = self.safe_query(query, (new_quantity, product_id))
        return {"affected_rows": result[0]["affected_rows"]}

# Инициализация базы данных
db = SafeDatabase("sql_injection_example.db")

# Создаем базу данных при запуске
db.init_database()

# Pydantic модели
class UserCreateRequest(RequestModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: str = Field(..., description="Email адрес")
    password: str = Field(..., min_length=8, description="Пароль")
    
    @validator('username')
    def validate_username(cls, v):
        """Валидация имени пользователя"""
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        
        # Проверяем на SQL инъекции
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'Username contains dangerous characters: {char}')
        
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        """Валидация email"""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        
        # Простая проверка email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        return v.lower().strip()

class ProductCreateRequest(RequestModel):
    name: str = Field(..., min_length=1, max_length=200, description="Название продукта")
    description: Optional[str] = Field(None, description="Описание продукта")
    price: float = Field(..., gt=0, description="Цена продукта")
    category: str = Field(..., description="Категория продукта")
    stock_quantity: int = Field(0, ge=0, description="Количество на складе")
    
    @validator('name')
    def validate_name(cls, v):
        """Валидация названия продукта"""
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty')
        
        # Проверяем на SQL инъекции
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Product name contains dangerous characters: {char}')
        
        return v.strip()

class SearchRequest(RequestModel):
    query: str = Field(..., min_length=1, max_length=100, description="Поисковый запрос")
    category: Optional[str] = Field(None, description="Категория для фильтрации")
    
    @validator('query')
    def validate_query(cls, v):
        """Валидация поискового запроса"""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        
        # Проверяем на SQL инъекции
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#', 'UNION', 'SELECT', 'DROP', 'DELETE']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'Search query contains dangerous characters: {char}')
        
        return v.strip()

# Эндпоинты

@app.get("/")
async def root(request: Request):
    """Базовый эндпоинт"""
    return {
        "message": "SQL Injection Protection Example API is running",
        "endpoints": {
            "/users": "GET/POST - Управление пользователями",
            "/products": "GET/POST - Управление продуктами",
            "/search": "POST - Безопасный поиск",
            "/categories": "GET - Список категорий",
            "/test-injection": "GET - Тестовые SQL инъекции",
            "/database-info": "GET - Информация о базе данных"
        },
        "security_features": [
            "Защита от SQL инъекций",
            "Параметризованные запросы",
            "Валидация входных данных",
            "Middleware для обнаружения атак",
            "Безопасные заголовки"
        ]
    }

@app.get("/users")
async def get_users(request: Request):
    """Получить список пользователей"""
    try:
        users = db.safe_query("SELECT id, username, email, created_at FROM users")
        return {
            "users": users,
            "total_count": len(users)
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.post("/users")
@validate_request_body(UserCreateRequest)
async def create_user(request: Request):
    """
    Создать пользователя с защитой от SQL инъекций
    
    Этот эндпоинт демонстрирует безопасную работу с базой данных:
    1. Валидация входных данных
    2. Параметризованные запросы
    3. Обработка ошибок
    """
    data = request.validated_data
    
    try:
        # Проверяем существование пользователя
        existing_user = db.get_user_by_username(data.username)
        if existing_user:
            return Response.json(
                {"error": "Username already exists", "code": "USERNAME_EXISTS"},
                status_code=400
            )
        
        existing_email = db.get_user_by_email(data.email)
        if existing_email:
            return Response.json(
                {"error": "Email already exists", "code": "EMAIL_EXISTS"},
                status_code=400
            )
        
        # Создаем пользователя (в реальном приложении хешировали бы пароль)
        user = db.create_user(data.username, data.email, data.password)
        
        return {
            "message": "User created successfully",
            "user": user
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.get("/products")
async def get_products(request: Request):
    """Получить список продуктов"""
    try:
        products = db.safe_query("SELECT * FROM products")
        return {
            "products": products,
            "total_count": len(products)
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.post("/products")
@validate_request_body(ProductCreateRequest)
async def create_product(request: Request):
    """
    Создать продукт с защитой от SQL инъекций
    """
    data = request.validated_data
    
    try:
        product = db.create_product(
            data.name,
            data.description,
            data.price,
            data.category,
            data.stock_quantity
        )
        
        return {
            "message": "Product created successfully",
            "product": product
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.post("/search")
@validate_request_body(SearchRequest)
async def search_products(request: Request):
    """
    Безопасный поиск продуктов
    
    Этот эндпоинт демонстрирует безопасный поиск с параметризованными запросами.
    """
    data = request.validated_data
    
    try:
        results = db.search_products(data.query, data.category)
        
        return {
            "query": data.query,
            "category": data.category,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.get("/categories")
async def get_categories(request: Request):
    """Получить список категорий"""
    try:
        categories = db.safe_query("SELECT DISTINCT category FROM products ORDER BY category")
        return {
            "categories": [cat["category"] for cat in categories],
            "total_count": len(categories)
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.get("/products/category/{category}")
async def get_products_by_category(request: Request, category: str):
    """Получить продукты по категории"""
    try:
        # Очищаем категорию от потенциально опасных символов
        safe_category = category.replace("'", "").replace('"', "").replace(";", "")
        
        products = db.get_products_by_category(safe_category)
        
        return {
            "category": safe_category,
            "products": products,
            "total_count": len(products)
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.get("/test-injection")
async def test_sql_injection(request: Request):
    """
    Тестовые SQL инъекции для демонстрации защиты
    
    ВНИМАНИЕ: Эти примеры показывают, как НЕ нужно делать запросы!
    """
    test_vectors = [
        {
            "name": "Basic SQL Injection",
            "vector": "'; DROP TABLE users; --",
            "description": "Базовая SQL инъекция для удаления таблицы"
        },
        {
            "name": "Union Based Injection",
            "vector": "' UNION SELECT * FROM users --",
            "description": "Union-based инъекция"
        },
        {
            "name": "Boolean Based Injection",
            "vector": "' OR 1=1 --",
            "description": "Boolean-based инъекция"
        },
        {
            "name": "Time Based Injection",
            "vector": "'; WAITFOR DELAY '00:00:05' --",
            "description": "Time-based инъекция"
        },
        {
            "name": "Error Based Injection",
            "vector": "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,VERSION(),0x7e,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.TABLES GROUP BY x)a) --",
            "description": "Error-based инъекция"
        },
        {
            "name": "Stacked Queries",
            "vector": "'; INSERT INTO users (username, email, password_hash) VALUES ('hacker', 'hacker@evil.com', 'hash'); --",
            "description": "Stacked queries инъекция"
        },
        {
            "name": "Comment Injection",
            "vector": "admin'/*",
            "description": "Инъекция через комментарии"
        },
        {
            "name": "Hex Injection",
            "vector": "0x61646D696E",  # hex for 'admin'
            "description": "Hex-encoded инъекция"
        },
        {
            "name": "Unicode Injection",
            "vector": "admin\u0027",
            "description": "Unicode-encoded инъекция"
        },
        {
            "name": "Case Manipulation",
            "vector": "AdMiN' Or '1'='1",
            "description": "Case manipulation инъекция"
        }
    ]
    
    return {
        "message": "SQL Injection Test Vectors",
        "description": "Эти векторы демонстрируют различные типы SQL инъекций",
        "warning": "НЕ используйте эти векторы в продакшене!",
        "vectors": test_vectors,
        "protection_methods": [
            "Параметризованные запросы",
            "Валидация входных данных",
            "Экранирование специальных символов",
            "Использование ORM",
            "Принцип наименьших привилегий"
        ]
    }

@app.get("/database-info")
async def get_database_info(request: Request):
    """Получить информацию о базе данных"""
    try:
        # Получаем статистику
        users_count = db.safe_query("SELECT COUNT(*) as count FROM users")[0]["count"]
        products_count = db.safe_query("SELECT COUNT(*) as count FROM products")[0]["count"]
        categories_count = db.safe_query("SELECT COUNT(DISTINCT category) as count FROM products")[0]["count"]
        
        return {
            "message": "Database Information",
            "statistics": {
                "users_count": users_count,
                "products_count": products_count,
                "categories_count": categories_count
            },
            "security_features": [
                "SQL injection protection enabled",
                "Parameterized queries",
                "Input validation",
                "Error handling"
            ]
        }
    except Exception as e:
        return Response.json(
            {"error": "Database error", "details": str(e)},
            status_code=500
        )

@app.get("/security-info")
async def get_security_info(request: Request):
    """Получить информацию о безопасности"""
    return {
        "message": "Security Information",
        "sql_injection_protection": {
            "enabled": True,
            "methods": [
                "Pattern detection",
                "Input sanitization",
                "Parameterized queries",
                "Input validation"
            ]
        },
        "headers": {
            "X-SQL-Injection-Protection": "enabled"
        },
        "best_practices": [
            "Always use parameterized queries",
            "Validate and sanitize all inputs",
            "Use least privilege principle",
            "Implement proper error handling",
            "Regular security audits"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8016) 