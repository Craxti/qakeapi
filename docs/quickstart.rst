Quickstart
==========

This guide will help you get started with QakeAPI.

Basic Application
---------------

Here's a simple example of a QakeAPI application:

.. code-block:: python

    from qakeapi import QakeAPI, Request, Response

    app = QakeAPI()

    @app.route("/")
    async def hello_world(request: Request) -> Response:
        return Response({"message": "Hello, World!"})

    @app.route("/items/{item_id}")
    async def get_item(request: Request, item_id: int) -> Response:
        return Response({
            "item_id": item_id,
            "message": f"Item {item_id} details"
        })

Running the Application
--------------------

Save the code in a file (e.g., `main.py`) and run it using uvicorn:

.. code-block:: bash

    uvicorn main:app --reload

Now you can access your API at http://localhost:8000.

Authentication
-------------

QakeAPI provides built-in authentication support:

.. code-block:: python

    from qakeapi import QakeAPI, Request, Response
    from qakeapi.auth import JWTAuth

    app = QakeAPI()
    auth = JWTAuth(secret_key="your-secret-key")

    @app.route("/protected")
    @auth.required
    async def protected_route(request: Request) -> Response:
        return Response({"message": "This is a protected route"})

Middleware
---------

Adding middleware is straightforward:

.. code-block:: python

    from qakeapi import QakeAPI, Middleware

    async def timing_middleware(request: Request, handler):
        start_time = time.time()
        response = await handler(request)
        duration = time.time() - start_time
        response.headers["X-Process-Time"] = str(duration)
        return response

    app = QakeAPI()
    app.add_middleware(timing_middleware) 