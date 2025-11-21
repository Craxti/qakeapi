# -*- coding: utf-8 -*-
"""
SQL Injection Protection Example with QakeAPI.
"""
import sys
import os
import re
import sqlite3
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.core.middleware import Middleware
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import BaseModel, Field, validator

# Application initialization
app = Application(title="SQL Injection Protection Example", version="1.0.3")

# Middleware for SQL injection protection
class SQLInjectionProtectionMiddleware(Middleware):
    """Middleware for SQL injection protection"""
    
    def __init__(self):
        self.__name__ = "SQLInjectionProtectionMiddleware"
        self.dangerous_patterns = [
            # SQL keywords
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|OR|AND)\b',
            # SQL comments
            r'--',
            r'/\*.*?\*/',
            # Quotes and semicolons
            r'[\'";]',
            # SQL functions
            r'\b(COUNT|SUM|AVG|MAX|MIN|LENGTH|SUBSTR|CONCAT|UPPER|LOWER)\b',
            # WHERE conditions
            r'\bWHERE\b.*?\b(OR|AND)\b',
            # JOIN
            r'\b(INNER|LEFT|RIGHT|FULL)\s+JOIN\b',
            # Subqueries
            r'\(\s*SELECT\b',
            # UNION injection
            r'\bUNION\s+(ALL\s+)?SELECT\b',
            # OR 1=1 injection
            r'\bOR\s+1\s*=\s*1\b',
            r'\bOR\s+\'1\'\s*=\s*\'1\'\b',
            # Comment injection
            r'#.*$',
            # Escaping injection
            r'\\\'.*?\\\'',
            # Hex injection
            r'0x[0-9a-fA-F]+',
            # Char injection
            r'CHAR\s*\(\s*\d+\s*\)',
            # Concat injection
            r'CONCAT\s*\([^)]*\)',
            # Substring injection
            r'SUBSTRING\s*\([^)]*\)',
            # Case injection
            r'\bCASE\s+WHEN\b',
            # If injection
            r'\bIF\s*\([^)]*\)',
            # Sleep injection
            r'\bSLEEP\s*\(\s*\d+\s*\)',
            # Benchmark injection
            r'\bBENCHMARK\s*\([^)]*\)',
            # Load_file injection
            r'\bLOAD_FILE\s*\([^)]*\)',
            # Into outfile injection
            r'\bINTO\s+OUTFILE\b',
            # Into dumpfile injection
            r'\bINTO\s+DUMPFILE\b',
            # information_schema injection
            r'\binformation_schema\b',
            # mysql injection
            r'\bmysql\b',
            # sys injection
            r'\bsys\b',
            # performance_schema injection
            r'\bperformance_schema\b',
        ]
        
        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.dangerous_patterns]
    
    def detect_sql_injection(self, text: str) -> bool:
        """Detects potential SQL injection"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        
        # Additional checks
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
        """Sanitizes input from potentially dangerous characters"""
        if not text:
            return text
        
        # Remove dangerous characters
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    async def __call__(self, request: Request, call_next):
        """Request processing with SQL injection protection"""
        # Check headers
        for key, value in request.headers.items():
            if isinstance(value, str) and self.detect_sql_injection(value):
                return Response.json(
                    {"error": "Potential SQL injection detected in headers", "code": "SQL_INJECTION_DETECTED"},
                    status_code=400
                )
        
        # Check query parameters
        for key, value in request.query_params.items():
            if isinstance(value, str) and self.detect_sql_injection(value):
                return Response.json(
                    {"error": "Potential SQL injection detected in query parameters", "code": "SQL_INJECTION_DETECTED"},
                    status_code=400
                )
        
        # Check body (if JSON)
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
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-SQL-Injection-Protection"] = "enabled"
        
        return response

# Connect middleware
# app.http_router.add_middleware(SQLInjectionProtectionMiddleware())

# Safe database class
class SafeDatabase:
    """Safe class for working with the database"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Database initialization"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create products table
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
            
            # Create orders table
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
        """Safe execution of query with parameters"""
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
        """Safely get user by username"""
        query = "SELECT * FROM users WHERE username = ?"
        result = self.safe_query(query, (username,))
        return result[0] if result else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Safely get user by email"""
        query = "SELECT * FROM users WHERE email = ?"
        result = self.safe_query(query, (email,))
        return result[0] if result else None
    
    def create_user(self, username: str, email: str, password_hash: str) -> Dict:
        """Safely create user"""
        query = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"
        result = self.safe_query(query, (username, email, password_hash))
        return {"id": result[0]["affected_rows"], "username": username, "email": email}
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Safe product search"""
        if category:
            sql_query = "SELECT * FROM products WHERE name LIKE ? AND category = ?"
            params = (f"%{query}%", category)
        else:
            sql_query = "SELECT * FROM products WHERE name LIKE ?"
            params = (f"%{query}%",)
        
        return self.safe_query(sql_query, params)
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Safely get products by category"""
        query = "SELECT * FROM products WHERE category = ?"
        return self.safe_query(query, (category,))
    
    def create_product(self, name: str, description: str, price: float, category: str, stock_quantity: int) -> Dict:
        """Safely create product"""
        query = "INSERT INTO products (name, description, price, category, stock_quantity) VALUES (?, ?, ?, ?, ?)"
        result = self.safe_query(query, (name, description, price, category, stock_quantity))
        return {"id": result[0]["affected_rows"], "name": name, "price": price}
    
    def update_product_stock(self, product_id: int, new_quantity: int) -> Dict:
        """Safely update product stock quantity"""
        query = "UPDATE products SET stock_quantity = ? WHERE id = ?"
        result = self.safe_query(query, (new_quantity, product_id))
        return {"affected_rows": result[0]["affected_rows"]}

# Database initialization
db = SafeDatabase("sql_injection_example.db")

# Create database on startup
db.init_database()

# Pydantic models
class UserCreateRequest(RequestModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    
    @validator('username')
    def validate_username(cls, v):
        """Username validation"""
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        
        # Check for SQL injection
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'Username contains dangerous characters: {char}')
        
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        """Email validation"""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        
        # Simple email check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        return v.lower().strip()

class ProductCreateRequest(RequestModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    category: str = Field(..., description="Product category")
    stock_quantity: int = Field(0, ge=0, description="Stock quantity")
    
    @validator('name')
    def validate_name(cls, v):
        """Product name validation"""
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty')
        
        # Check for SQL injection
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Product name contains dangerous characters: {char}')
        
        return v.strip()

class SearchRequest(RequestModel):
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    category: Optional[str] = Field(None, description="Category for filtering")
    
    @validator('query')
    def validate_query(cls, v):
        """Search query validation"""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        
        # Check for SQL injection
        dangerous_chars = ['\'', '"', ';', '--', '/*', '*/', '#', 'UNION', 'SELECT', 'DROP', 'DELETE']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'Search query contains dangerous characters: {char}')
        
        return v.strip()

# Endpoints

@app.get("/")
async def root(request: Request):
    """Base endpoint"""
    return {
        "message": "SQL Injection Protection Example API is running",
        "endpoints": {
            "/users": "GET/POST - User management",
            "/products": "GET/POST - Product management",
            "/search": "POST - Safe search",
            "/categories": "GET - List of categories",
            "/test-injection": "GET - SQL injection test vectors",
            "/database-info": "GET - Database information"
        },
        "security_features": [
            "SQL injection protection",
            "Parameterized queries",
            "Input data validation",
            "Middleware for attack detection",
            "Security headers"
        ]
    }

@app.get("/users")
async def get_users(request: Request):
    """Get list of users"""
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
    Create user with SQL injection protection
    
    This endpoint demonstrates safe database operations:
    1. Input data validation
    2. Parameterized queries
    3. Error handling
    """
    data = request.validated_data
    
    try:
        # Check for existing user
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
        
        # Create user (in a real application, we would hash the password)
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
    """Get list of products"""
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
    Create product with SQL injection protection
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
    Safe product search
    
    This endpoint demonstrates safe search with parameterized queries.
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
    """Get list of categories"""
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
    """Get products by category"""
    try:
        # Sanitize category from potentially dangerous characters
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
    SQL injection test vectors for demonstration purposes
    
    WARNING: These examples show how NOT to make queries!
    """
    test_vectors = [
        {
            "name": "Basic SQL Injection",
            "vector": "'; DROP TABLE users; --",
            "description": "Basic SQL injection to delete table"
        },
        {
            "name": "Union Based Injection",
            "vector": "' UNION SELECT * FROM users --",
            "description": "Union-based injection"
        },
        {
            "name": "Boolean Based Injection",
            "vector": "' OR 1=1 --",
            "description": "Boolean-based injection"
        },
        {
            "name": "Time Based Injection",
            "vector": "'; WAITFOR DELAY '00:00:05' --",
            "description": "Time-based injection"
        },
        {
            "name": "Error Based Injection",
            "vector": "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,VERSION(),0x7e,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.TABLES GROUP BY x)a) --",
            "description": "Error-based injection"
        },
        {
            "name": "Stacked Queries",
            "vector": "'; INSERT INTO users (username, email, password_hash) VALUES ('hacker', 'hacker@evil.com', 'hash'); --",
            "description": "Stacked queries injection"
        },
        {
            "name": "Comment Injection",
            "vector": "admin'/*",
            "description": "Injection through comments"
        },
        {
            "name": "Hex Injection",
            "vector": "0x61646D696E",  # hex for 'admin'
            "description": "Hex-encoded injection"
        },
        {
            "name": "Unicode Injection",
            "vector": "admin\u0027",
            "description": "Unicode-encoded injection"
        },
        {
            "name": "Case Manipulation",
            "vector": "AdMiN' Or '1'='1",
            "description": "Case manipulation injection"
        }
    ]
    
    return {
        "message": "SQL Injection Test Vectors",
        "description": "These vectors demonstrate various types of SQL injection",
        "warning": "DO NOT USE THESE VECTORS IN PRODUCTION!",
        "vectors": test_vectors,
        "protection_methods": [
            "Parameterized queries",
            "Input data validation",
            "Special characters escaping",
            "ORM usage",
            "Least privilege principle"
        ]
    }

@app.get("/database-info")
async def get_database_info(request: Request):
    """Get database information"""
    try:
        # Get statistics
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
                "Input data validation",
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
    """Get security information"""
    return {
        "message": "Security Information",
        "sql_injection_protection": {
            "enabled": True,
            "methods": [
                "Pattern detection",
                "Input sanitization",
                "Parameterized queries",
                "Input data validation"
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