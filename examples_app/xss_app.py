# -*- coding: utf-8 -*-
"""
XSS Protection Example with QakeAPI.
"""
import sys
import os
import html
import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote, unquote

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.core.middleware import Middleware
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import BaseModel, Field, validator

# Application initialization
app = Application(title="XSS Protection Example", version="1.0.3")

# Pydantic models with XSS validation
class CommentRequest(RequestModel):
    """Model for comment with XSS protection"""
    author: str = Field(..., min_length=1, max_length=100, description="Comment author")
    content: str = Field(..., min_length=1, max_length=1000, description="Comment content")
    email: Optional[str] = Field(None, description="Author email")
    website: Optional[str] = Field(None, description="Author website")
    
    @validator('author')
    def validate_author(cls, v):
        """Author name validation"""
        if not v or not v.strip():
            raise ValueError('Author name cannot be empty')
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'javascript:', 'onload', 'onerror']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'Author name contains dangerous characters: {char}')
        
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Comment content validation"""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        
        # Check for HTML tags
        if re.search(r'<[^>]+>', v):
            raise ValueError('Content cannot contain HTML tags')
        
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        """Email validation"""
        if v is None:
            return v
        
        # Simple email check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        return v.lower()
    
    @validator('website')
    def validate_website(cls, v):
        """Website validation"""
        if v is None:
            return v
        
        # Check protocol
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        # Simple URL check
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid website URL')
        
        return v

class MessageRequest(RequestModel):
    """Model for message"""
    title: str = Field(..., min_length=1, max_length=200, description="Message title")
    message: str = Field(..., min_length=1, max_length=5000, description="Message text")
    recipient: str = Field(..., description="Recipient")

class SearchRequest(RequestModel):
    """Model for search"""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    category: Optional[str] = Field(None, description="Category")

# Database simulation
comments_db = []
messages_db = []
search_history = []

# Endpoints

@app.get("/")
async def root(request: Request):
    """Base endpoint"""
    return {
        "message": "XSS Protection Example API is running",
        "endpoints": {
            "/comments": "GET/POST - Comment management",
            "/messages": "POST - Send messages",
            "/search": "POST - Search with protection",
            "/preview": "POST - Content preview",
            "/sanitize": "POST - Text sanitization",
            "/test-xss": "GET - XSS test vectors"
        },
        "security_features": [
            "Automatic HTML sanitization",
            "Input data validation",
            "XSS attack protection",
            "Content Security Policy",
            "Security headers"
        ]
    }

@app.get("/comments")
async def get_comments(request: Request):
    """Get list of comments"""
    return {
        "comments": comments_db,
        "total_count": len(comments_db)
    }

@app.post("/comments")
@validate_request_body(CommentRequest)
async def create_comment(request: Request):
    """
    Create comment with XSS protection
    
    This endpoint demonstrates XSS attack protection:
    1. Input data validation
    2. HTML sanitization
    3. Safe display
    """
    data = request.validated_data
    
    # Additional data sanitization
    sanitized_comment = {
        "id": len(comments_db) + 1,
        "author": html.escape(data.author),
        "content": html.escape(data.content),
        "email": html.escape(data.email) if data.email else None,
        "website": data.website,  # URL already validated
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
    Send message with XSS protection
    """
    data = request.validated_data
    
    # Sanitize data
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
    Search with XSS protection
    """
    data = request.validated_data
    
    # Sanitize search query
    sanitized_query = html.escape(data.query)
    
    # Simulate search
    search_results = [
        {
            "id": 1,
            "title": f"Result for: {sanitized_query}",
            "content": f"This is a search result for '{sanitized_query}'",
            "url": f"https://example.com/search?q={quote(sanitized_query)}"
        }
    ]
    
    # Save to history
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
    Content preview with XSS protection
    """
    try:
        body = await request.json()
        content = body.get("content", "")
        
        # Sanitize content
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
    Sanitize text from potentially dangerous content
    """
    try:
        body = await request.json()
        text = body.get("text", "")
        
        # Get middleware
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
        
        # Sanitize text
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
    XSS test vectors for protection demonstration
    """
    test_vectors = [
        {
            "name": "Basic Script Tag",
            "vector": "<script>alert('XSS')</script>",
            "description": "Basic script tag"
        },
        {
            "name": "JavaScript Protocol",
            "vector": "javascript:alert('XSS')",
            "description": "JavaScript protocol in URL"
        },
        {
            "name": "Event Handler",
            "vector": "<img src=x onerror=alert('XSS')>",
            "description": "onerror event handler"
        },
        {
            "name": "Iframe Injection",
            "vector": "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "description": "Iframe injection"
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
            "description": "Mixed case"
        },
        {
            "name": "Nested Tags",
            "vector": "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
            "description": "Nested tags"
        },
        {
            "name": "Null Byte",
            "vector": "<script>alert('XSS')</script>",
            "description": "Null byte injection"
        }
    ]
    
    return {
        "message": "XSS Test Vectors",
        "description": "These vectors are used for testing XSS protection",
        "vectors": test_vectors,
        "warning": "Do not use these vectors in production!"
    }

@app.get("/search-history")
async def get_search_history(request: Request):
    """Get search history"""
    return {
        "search_history": search_history[-10:],  # Last 10 requests
        "total_searches": len(search_history)
    }

@app.get("/security-headers")
async def get_security_headers(request: Request):
    """Get security headers information"""
    return {
        "message": "Security Headers Information",
        "headers": {
            "X-XSS-Protection": "1; mode=block",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        },
        "description": "These headers are added automatically by middleware"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8015) 