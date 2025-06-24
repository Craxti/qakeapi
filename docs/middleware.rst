Middleware
==========

QakeAPI provides a flexible middleware system that allows you to modify requests and responses.

Basic Usage
----------

Here's a simple example of a timing middleware:

.. code-block:: python

    from qakeapi import QakeAPI
    import time

    app = QakeAPI()

    async def timing_middleware(request, handler):
        start_time = time.time()
        response = await handler(request)
        duration = time.time() - start_time
        response.headers["X-Process-Time"] = str(duration)
        return response

    app.add_middleware(timing_middleware)

Built-in Middleware
-----------------

CORS Middleware
~~~~~~~~~~~~~

.. code-block:: python

    from qakeapi.middleware import CORS

    cors = CORS(
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"]
    )
    app.add_middleware(cors)

Rate Limiting
~~~~~~~~~~~

.. code-block:: python

    from qakeapi.middleware import RateLimiter

    limiter = RateLimiter(requests=100, window=60)
    app.add_middleware(limiter)

Authentication
~~~~~~~~~~~~

.. code-block:: python

    from qakeapi.middleware import JWTMiddleware

    jwt = JWTMiddleware(secret_key="your-secret")
    app.add_middleware(jwt)

Creating Custom Middleware
-----------------------

Middleware functions should be async and accept two parameters:

1. ``request``: The incoming request object
2. ``handler``: The next handler in the chain

Example:

.. code-block:: python

    async def logging_middleware(request, handler):
        print(f"Request to {request.url}")
        response = await handler(request)
        print(f"Response status: {response.status_code}")
        return response

    app.add_middleware(logging_middleware)

Middleware Order
-------------

Middleware is executed in the order it was added. The first middleware added
will be the outermost in the request-response cycle. 