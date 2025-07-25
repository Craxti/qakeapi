Middleware Guide
================

Middleware in QakeAPI allows you to process requests and responses in a chain, enabling cross-cutting concerns like authentication, logging, CORS, and more.

.. contents:: Table of Contents
   :local:

Built-in Middleware
------------------

QakeAPI comes with several built-in middleware components:

CORS Middleware
~~~~~~~~~~~~~~~

Handles Cross-Origin Resource Sharing (CORS) for web applications.

.. code-block:: python

   from qakeapi import Application
   from qakeapi.middleware import CORSMiddleware

   app = Application()

   # Basic CORS setup
   cors = CORSMiddleware(
       allow_origins=["http://localhost:3000", "https://myapp.com"],
       allow_methods=["GET", "POST", "PUT", "DELETE"],
       allow_headers=["*"],
       allow_credentials=True
   )
   app.add_middleware(cors)

   @app.get("/api/data")
   async def get_data():
       return {"data": "sensitive information"}

Rate Limiting Middleware
~~~~~~~~~~~~~~~~~~~~~~~~

Limits the number of requests per time period to prevent abuse.

.. code-block:: python

   from qakeapi.security import RateLimiter

   # Global rate limiting
   limiter = RateLimiter(requests_per_minute=60)
   app.add_middleware(limiter)

   # Per-endpoint rate limiting
   @app.get("/api/sensitive")
   @limiter.limit(requests_per_minute=10)
   async def get_sensitive_data():
       return {"data": "very sensitive"}

Authentication Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~

Provides authentication for protected routes.

.. code-block:: python

   from qakeapi.security import JWTAuthBackend, requires_auth

   auth = JWTAuthBackend(secret_key="your-secret-key")
   app.add_middleware(auth)

   @app.get("/protected")
   @requires_auth(auth)
   async def protected_route():
       return {"message": "This is protected!"}

Creating Custom Middleware
-------------------------

You can create custom middleware by implementing the middleware interface:

.. code-block:: python

   class CustomMiddleware:
       def __init__(self, custom_header: str = "X-Custom"):
           self.custom_header = custom_header

       async def __call__(self, request, handler):
           # Pre-processing
           print(f"Request to: {request.path}")
           start_time = time.time()

           # Call next handler
           response = await handler(request)

           # Post-processing
           response.headers[self.custom_header] = "QakeAPI"
           response.headers["X-Response-Time"] = str(time.time() - start_time)
           
           return response

   # Add to application
   app.add_middleware(CustomMiddleware("X-MyApp"))

Middleware Order
---------------

Middleware is executed in the order it's added. The first middleware added is the outermost layer:

.. code-block:: python

   app = Application()

   # Order: CORS → Rate Limiting → Authentication → Your Routes
   app.add_middleware(CORSMiddleware(allow_origins=["*"]))
   app.add_middleware(RateLimiter(requests_per_minute=60))
   app.add_middleware(JWTAuthBackend(secret_key="secret"))

   @app.get("/")
   async def hello():
       return {"message": "Hello"}

Request Flow with Middleware
---------------------------

.. code-block:: text

   Client Request
        ↓
   ┌─────────────────┐
   │   CORS          │ ← Check origin, add CORS headers
   └─────────────────┘
        ↓
   ┌─────────────────┐
   │ Rate Limiting   │ ← Check rate limits
   └─────────────────┘
        ↓
   ┌─────────────────┐
   │ Authentication  │ ← Verify JWT token
   └─────────────────┘
        ↓
   ┌─────────────────┐
   │   Your Route    │ ← Execute your handler
   └─────────────────┘
        ↓
   ┌─────────────────┐
   │ Authentication  │ ← Add auth headers
   └─────────────────┘
        ↓
   ┌─────────────────┐
   │ Rate Limiting   │ ← Update rate limit counters
   └─────────────────┘
        ↓
   ┌─────────────────┐
   │   CORS          │ ← Add CORS headers to response
   └─────────────────┘
        ↓
   Client Response

Advanced Middleware Examples
---------------------------

Logging Middleware
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   import time
   from typing import Dict, Any

   class LoggingMiddleware:
       def __init__(self, logger: logging.Logger = None):
           self.logger = logger or logging.getLogger(__name__)

       async def __call__(self, request, handler):
           start_time = time.time()
           
           # Log request
           self.logger.info(f"Request: {request.method} {request.path}")
           
           try:
               response = await handler(request)
               duration = time.time() - start_time
               
               # Log response
               self.logger.info(
                   f"Response: {response.status_code} "
                   f"({duration:.3f}s)"
               )
               
               return response
           except Exception as e:
               duration = time.time() - start_time
               self.logger.error(
                   f"Error: {e} ({duration:.3f}s)"
               )
               raise

   app.add_middleware(LoggingMiddleware())

Performance Monitoring Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   from collections import defaultdict

   class PerformanceMiddleware:
       def __init__(self):
           self.metrics = defaultdict(list)

       async def __call__(self, request, handler):
           start_time = time.time()
           
           response = await handler(request)
           
           duration = time.time() - start_time
           self.metrics[request.path].append(duration)
           
           # Add performance headers
           response.headers["X-Response-Time"] = f"{duration:.3f}s"
           response.headers["X-Avg-Response-Time"] = f"{self.get_avg_time(request.path):.3f}s"
           
           return response

       def get_avg_time(self, path: str) -> float:
           times = self.metrics[path]
           return sum(times) / len(times) if times else 0

   app.add_middleware(PerformanceMiddleware())

Error Handling Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from qakeapi import Response

   class ErrorHandlingMiddleware:
       async def __call__(self, request, handler):
           try:
               return await handler(request)
           except ValueError as e:
               return Response.json(
                   {"error": "Validation error", "details": str(e)},
                   status_code=400
               )
           except PermissionError as e:
               return Response.json(
                   {"error": "Permission denied", "details": str(e)},
                   status_code=403
               )
           except Exception as e:
               return Response.json(
                   {"error": "Internal server error"},
                   status_code=500
               )

   app.add_middleware(ErrorHandlingMiddleware())

Conditional Middleware
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ConditionalMiddleware:
       def __init__(self, condition_func, middleware):
           self.condition_func = condition_func
           self.middleware = middleware

       async def __call__(self, request, handler):
           if self.condition_func(request):
               return await self.middleware(request, handler)
           return await handler(request)

   # Only apply rate limiting to API routes
   def is_api_route(request):
       return request.path.startswith("/api/")

   api_limiter = ConditionalMiddleware(
       is_api_route,
       RateLimiter(requests_per_minute=30)
   )
   app.add_middleware(api_limiter)

Testing Middleware
-----------------

You can test middleware using the testing utilities:

.. code-block:: python

   import pytest
   from qakeapi.testing import TestClient

   @pytest.mark.asyncio
   async def test_cors_middleware():
       app = Application()
       app.add_middleware(CORSMiddleware(allow_origins=["http://localhost:3000"]))
       
       @app.get("/")
       async def hello():
           return {"message": "Hello"}

       client = TestClient(app)
       response = await client.get("/", headers={"Origin": "http://localhost:3000"})
       
       assert response.status_code == 200
       assert "Access-Control-Allow-Origin" in response.headers

   @pytest.mark.asyncio
   async def test_rate_limiting_middleware():
       app = Application()
       app.add_middleware(RateLimiter(requests_per_minute=2))
       
       @app.get("/")
       async def hello():
           return {"message": "Hello"}

       client = TestClient(app)
       
       # First two requests should succeed
       response1 = await client.get("/")
       response2 = await client.get("/")
       
       assert response1.status_code == 200
       assert response2.status_code == 200
       
       # Third request should be rate limited
       response3 = await client.get("/")
       assert response3.status_code == 429

Best Practices
--------------

1. **Order Matters**: Add middleware in the order you want them executed
2. **Keep It Simple**: Each middleware should have a single responsibility
3. **Handle Errors**: Always handle exceptions in your middleware
4. **Performance**: Avoid expensive operations in middleware
5. **Testing**: Test your middleware in isolation
6. **Documentation**: Document what your middleware does and its configuration

Common Patterns
---------------

Request/Response Transformation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class RequestTransformMiddleware:
       async def __call__(self, request, handler):
           # Transform request
           if request.headers.get("content-type") == "application/xml":
               # Convert XML to JSON
               request.body = self.xml_to_json(request.body)
               request.headers["content-type"] = "application/json"
           
           response = await handler(request)
           
           # Transform response
           if request.headers.get("accept") == "application/xml":
               response.body = self.json_to_xml(response.body)
               response.headers["content-type"] = "application/xml"
           
           return response

Context Injection
~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ContextMiddleware:
       async def __call__(self, request, handler):
           # Add context to request
           request.context = {
               "user_id": self.extract_user_id(request),
               "request_id": self.generate_request_id(),
               "timestamp": time.time()
           }
           
           return await handler(request)

   # In your handlers
   @app.get("/user")
   async def get_user(request):
       user_id = request.context["user_id"]
       return {"user_id": user_id} 