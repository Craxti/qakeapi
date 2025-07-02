# -*- coding: utf-8 -*-
"""
OpenAPI/Swagger example with QakeAPI.
"""
import sys
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import BaseModel, Field, EmailStr, HttpUrl

# Initialize application with extended OpenAPI documentation
app = Application(
    title="OpenAPI/Swagger Example",
    version="1.0.3",
    description="""
    ## API Example with Full OpenAPI Documentation
    
    This API demonstrates QakeAPI capabilities for generating OpenAPI/Swagger documentation.
    
    ### Features:
    * Automatic schema generation
    * Custom Pydantic models
    * Request and response validation
    * Request and response examples
    * Endpoint grouping by tags
    * Error descriptions
    
    ### Authentication:
    API uses Bearer tokens for authentication.
    """
)

# Enum for statuses
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Pydantic models with full documentation
class UserBase(RequestModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full user name")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")

class UserCreate(UserBase):
    """Model for creating user"""
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Password confirmation")

class UserUpdate(RequestModel):
    """Model for updating user"""
    email: Optional[EmailStr] = Field(None, description="New email address")
    full_name: Optional[str] = Field(None, max_length=100, description="New full name")
    age: Optional[int] = Field(None, ge=0, le=150, description="New age")
    status: Optional[UserStatus] = Field(None, description="New user status")

class UserResponse(UserBase):
    """User response model"""
    id: int = Field(..., description="Unique user identifier")
    status: UserStatus = Field(..., description="User status")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

class ProductBase(RequestModel):
    """Base product model"""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    category: str = Field(..., description="Product category")

class ProductCreate(ProductBase):
    """Model for creating product"""
    stock_quantity: int = Field(..., ge=0, description="Stock quantity")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")

class ProductUpdate(RequestModel):
    """Model for updating product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="New name")
    description: Optional[str] = Field(None, description="New description")
    price: Optional[float] = Field(None, gt=0, description="New price")
    category: Optional[str] = Field(None, description="New category")
    stock_quantity: Optional[int] = Field(None, ge=0, description="New stock quantity")
    image_url: Optional[HttpUrl] = Field(None, description="New image URL")

class ProductResponse(ProductBase):
    """Product response model"""
    id: int = Field(..., description="Unique product identifier")
    stock_quantity: int = Field(..., description="Stock quantity")
    image_url: Optional[str] = Field(None, description="Image URL")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

class OrderItem(RequestModel):
    """Order item model"""
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity")

class OrderCreate(RequestModel):
    """Model for creating order"""
    items: List[OrderItem] = Field(..., min_items=1, description="Order items list")
    shipping_address: str = Field(..., description="Shipping address")
    notes: Optional[str] = Field(None, description="Additional notes")

class OrderResponse(RequestModel):
    """Order response model"""
    id: int = Field(..., description="Unique order identifier")
    user_id: int = Field(..., description="User ID")
    items: List[OrderItem] = Field(..., description="Order items")
    total_amount: float = Field(..., description="Total order amount")
    status: OrderStatus = Field(..., description="Order status")
    shipping_address: str = Field(..., description="Shipping address")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="Creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

class ErrorResponse(RequestModel):
    """Error model"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")

class PaginationParams(RequestModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")

class SearchParams(RequestModel):
    """Search parameters"""
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[str] = Field(None, description="Category filter")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")

# Database simulation
users_db = {}
products_db = {}
orders_db = {}
next_user_id = 1
next_product_id = 1
next_order_id = 1

# Endpoints with full documentation

@app.get("/", tags=["General"])
async def root(request: Request):
    """
    Base endpoint
    
    Returns API information and available endpoints.
    """
    return {
        "message": "OpenAPI/Swagger Example API is running",
        "version": "1.0.2",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "endpoints": {
            "users": "/users - User management",
            "products": "/products - Product management", 
            "orders": "/orders - Order management",
            "search": "/search - Product search"
        }
    }

@app.post("/users", tags=["Users"], response_model=UserResponse, status_code=201)
@validate_request_body(UserCreate)
async def create_user(request: Request):
    """
    Create new user
    
    Creates a new user in the system.
    
    - **username**: Unique username
    - **email**: Email address
    - **password**: Password (minimum 8 characters)
    - **confirm_password**: Password confirmation
    """
    global next_user_id
    user_data = request.validated_data
    
    # Check passwords
    if user_data.password != user_data.confirm_password:
        return Response.json(
            {"error": "Passwords do not match", "code": "PASSWORD_MISMATCH"},
            status_code=400
        )
    
    # Check username uniqueness
    if any(u["username"] == user_data.username for u in users_db.values()):
        return Response.json(
            {"error": "Username already exists", "code": "USERNAME_EXISTS"},
            status_code=400
        )
    
    # Create user
    user = {
        "id": next_user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "age": user_data.age,
        "status": UserStatus.ACTIVE,
        "created_at": datetime.utcnow(),
        "updated_at": None
    }
    
    users_db[next_user_id] = user
    next_user_id += 1
    
    return user

@app.get("/users", tags=["Users"])
async def list_users(request: Request):
    """
    Get users list
    
    Returns list of all users.
    """
    return list(users_db.values())

@app.get("/users/{user_id}", tags=["Users"], response_model=UserResponse)
async def get_user(request: Request, user_id: int):
    """
    Get user by ID
    
    Returns user information by unique identifier.
    
    - **user_id**: Unique user identifier
    """
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found", "code": "USER_NOT_FOUND"},
            status_code=404
        )
    
    return users_db[user_id]

@app.post("/products", tags=["Products"], response_model=ProductResponse, status_code=201)
@validate_request_body(ProductCreate)
async def create_product(request: Request):
    """
    Create new product
    
    Creates a new product in the system.
    """
    global next_product_id
    product_data = request.validated_data
    
    product = {
        "id": next_product_id,
        "name": product_data.name,
        "description": product_data.description,
        "price": product_data.price,
        "category": product_data.category,
        "stock_quantity": product_data.stock_quantity,
        "image_url": str(product_data.image_url) if product_data.image_url else None,
        "created_at": datetime.utcnow(),
        "updated_at": None
    }
    
    products_db[next_product_id] = product
    next_product_id += 1
    
    return product

@app.get("/products", tags=["Products"])
async def list_products(request: Request):
    """
    Get products list
    
    Returns list of all products.
    """
    return list(products_db.values())

@app.get("/products/{product_id}", tags=["Products"], response_model=ProductResponse)
async def get_product(request: Request, product_id: int):
    """
    Get product by ID
    
    Returns product information by unique identifier.
    
    - **product_id**: Unique product identifier
    """
    if product_id not in products_db:
        return Response.json(
            {"error": "Product not found", "code": "PRODUCT_NOT_FOUND"},
            status_code=404
        )
    
    return products_db[product_id]

@app.get("/search", tags=["Search"])
async def search_products(request: Request, search: SearchParams = None):
    """
    Search products
    
    Performs product search by various criteria.
    
    - **query**: Search query
    - **category**: Category filter
    - **min_price**: Minimum price
    - **max_price**: Maximum price
    """
    if not search:
        search = SearchParams()
    
    products = list(products_db.values())
    
    # Filter by query
    if search.query:
        products = [p for p in products if search.query.lower() in p["name"].lower()]
    
    # Filter by category
    if search.category:
        products = [p for p in products if p["category"].lower() == search.category.lower()]
    
    # Filter by price
    if search.min_price is not None:
        products = [p for p in products if p["price"] >= search.min_price]
    
    if search.max_price is not None:
        products = [p for p in products if p["price"] <= search.max_price]
    
    return products

@app.post("/orders", tags=["Orders"], response_model=OrderResponse, status_code=201)
@validate_request_body(OrderCreate)
async def create_order(request: Request):
    """
    Create new order
    
    Creates a new order in the system.
    """
    global next_order_id
    order_data = request.validated_data
    
    # Check product availability
    total_amount = 0
    for item in order_data.items:
        if item.product_id not in products_db:
            return Response.json(
                {"error": f"Product {item.product_id} not found", "code": "PRODUCT_NOT_FOUND"},
                status_code=404
            )
        
        product = products_db[item.product_id]
        if product["stock_quantity"] < item.quantity:
            return Response.json(
                {"error": f"Insufficient stock for product {item.product_id}", "code": "INSUFFICIENT_STOCK"},
                status_code=400
            )
        
        total_amount += product["price"] * item.quantity
    
    order = {
        "id": next_order_id,
        "user_id": 1,  # In real app would get from token
        "items": [item.dict() for item in order_data.items],
        "total_amount": total_amount,
        "status": OrderStatus.PENDING,
        "shipping_address": order_data.shipping_address,
        "notes": order_data.notes,
        "created_at": datetime.utcnow(),
        "updated_at": None
    }
    
    orders_db[next_order_id] = order
    next_order_id += 1
    
    return order

@app.get("/orders", tags=["Orders"])
async def list_orders(request: Request, pagination: PaginationParams = None):
    """
    Get orders list
    
    Returns list of all orders with pagination.
    
    - **page**: Page number (default 1)
    - **size**: Page size (default 10, maximum 100)
    """
    if not pagination:
        pagination = PaginationParams()
    
    orders = list(orders_db.values())
    start = (pagination.page - 1) * pagination.size
    end = start + pagination.size
    
    return orders[start:end]

@app.get("/orders/{order_id}", tags=["Orders"], response_model=OrderResponse)
async def get_order(request: Request, order_id: int):
    """
    Get order by ID
    
    Returns order information by unique identifier.
    
    - **order_id**: Unique order identifier
    """
    if order_id not in orders_db:
        return Response.json(
            {"error": "Order not found", "code": "ORDER_NOT_FOUND"},
            status_code=404
        )
    
    return orders_db[order_id]

@app.get("/health", tags=["System"])
async def health_check(request: Request):
    """
    API health check
    
    Returns API health status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.2"
    }

@app.put("/users/{user_id}", tags=["Users"], response_model=UserResponse)
@validate_request_body(UserUpdate)
async def update_user(request: Request, user_id: int):
    """
    Update user
    
    Updates user information.
    
    - **user_id**: Unique user identifier
    """
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found", "code": "USER_NOT_FOUND"},
            status_code=404
        )
    
    user_data = request.validated_data
    user = users_db[user_id]
    
    # Update fields
    for field, value in user_data.dict(exclude_unset=True).items():
        user[field] = value
    
    user["updated_at"] = datetime.utcnow()
    
    return user

@app.delete("/users/{user_id}", tags=["Users"], status_code=204)
async def delete_user(request: Request, user_id: int):
    """
    Delete user
    
    Deletes user from system.
    
    - **user_id**: Unique user identifier
    """
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found", "code": "USER_NOT_FOUND"},
            status_code=404
        )
    
    del users_db[user_id]
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8013) 