"""
OpenAPI schema generation.

This module provides OpenAPI 3.0 schema generation for API documentation.
"""

import json
import inspect
from typing import Any, Dict, List, Optional
from .router import Router, Route


class OpenAPIGenerator:
    """
    OpenAPI schema generator.

    Generates OpenAPI 3.0 schema from registered routes.
    """

    def __init__(
        self,
        title: str = "API",
        version: str = "1.0.0",
        description: str = "",
        servers: Optional[List[Dict[str, str]]] = None,
    ):
        """
        Initialize OpenAPI generator.

        Args:
            title: API title
            version: API version
            description: API description
            servers: List of server URLs
        """
        self.title = title
        self.version = version
        self.description = description
        self.servers = servers or [{"url": "/"}]

    def generate_schema(self, router: Router) -> Dict[str, Any]:
        """
        Generate OpenAPI schema from router.

        Args:
            router: Router instance

        Returns:
            OpenAPI schema dictionary
        """
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "servers": self.servers,
            "paths": {},
            "components": {
                "schemas": {},
            },
        }

        # Process routes
        for route in router.routes:
            path = route.path
            if path not in schema["paths"]:
                schema["paths"][path] = {}

            # Convert path parameters to OpenAPI format
            openapi_path = self._convert_path_params(path)

            # Add operation for each method
            for method in route.methods:
                method_lower = method.lower()
                operation = self._generate_operation(route, method)
                schema["paths"][openapi_path][method_lower] = operation

        return schema

    def _convert_path_params(self, path: str) -> str:
        """
        Convert route path to OpenAPI path format.

        Args:
            path: Route path (e.g., "/users/{user_id}")

        Returns:
            OpenAPI path format
        """
        # Already in OpenAPI format
        return path

    def _generate_operation(self, route: Route, method: str) -> Dict[str, Any]:
        """
        Generate OpenAPI operation from route.

        Args:
            route: Route instance
            method: HTTP method

        Returns:
            OpenAPI operation dictionary
        """
        operation = {
            "summary": route.name or f"{method} {route.path}",
            "operationId": route.name
            or f"{method.lower()}_{route.path.replace('/', '_').replace('{', '').replace('}', '')}",
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"},
                        },
                    },
                },
                "201": {
                    "description": "Created",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"},
                        },
                    },
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "422": {
                    "description": "Validation error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {"type": "string"},
                                    "field": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        }

        # Add path parameters
        if route.param_names:
            operation["parameters"] = []
            for param_name in route.param_names:
                operation["parameters"].append(
                    {
                        "name": param_name,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                )

        # Add request body for POST, PUT, PATCH methods
        if method.upper() in ("POST", "PUT", "PATCH"):
            request_body = self._generate_request_body(route.handler)
            if request_body:
                operation["requestBody"] = request_body

        return operation

    def _generate_request_body(self, handler: Any) -> Optional[Dict[str, Any]]:
        """
        Generate request body schema from handler signature.

        Args:
            handler: Handler function

        Returns:
            Request body schema or None
        """
        try:
            sig = inspect.signature(handler)

            # Find BaseModel parameter
            for param_name, param in sig.parameters.items():
                param_type = param.annotation

                # Skip if no annotation
                if param_type == inspect.Parameter.empty:
                    continue

                # Check if it's a BaseModel subclass
                is_basemodel = False
                if inspect.isclass(param_type):
                    # Check MRO for BaseModel
                    for base in param_type.__mro__:
                        if base != object and hasattr(base, "_get_fields"):
                            is_basemodel = True
                            break

                if is_basemodel:
                    # Generate schema for this model
                    schema_ref = self._generate_model_schema(param_type)

                    return {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": schema_ref,
                            },
                        },
                        "description": f"Request body for {param_type.__name__}",
                    }
        except Exception:
            # If we can't analyze handler, return None
            pass

        return None

    def _generate_model_schema(self, model_class: Any) -> Dict[str, Any]:
        """
        Generate OpenAPI schema for BaseModel.

        Args:
            model_class: BaseModel class

        Returns:
            Schema reference or inline schema
        """
        # Get model name
        model_name = model_class.__name__

        # Check if we already have this schema
        # For now, generate inline schema
        try:
            fields = model_class._get_fields()
            properties = {}
            required = []

            for field_name, field_def in fields.items():
                # Determine field type
                field_type = "string"  # default
                field_format = None

                if field_def.validator:
                    validator_type = type(field_def.validator).__name__
                    if (
                        "String" in validator_type
                        or "Email" in validator_type
                        or "URL" in validator_type
                    ):
                        field_type = "string"
                        if "Email" in validator_type:
                            field_format = "email"
                        elif "URL" in validator_type:
                            field_format = "uri"
                    elif "Integer" in validator_type:
                        field_type = "integer"
                    elif "Float" in validator_type:
                        field_type = "number"
                        field_format = "float"
                    elif "Boolean" in validator_type:
                        field_type = "boolean"
                    elif "DateTime" in validator_type:
                        field_type = "string"
                        field_format = "date-time"

                field_schema = {"type": field_type}
                if field_format:
                    field_schema["format"] = field_format

                properties[field_name] = field_schema

                if field_def.required:
                    required.append(field_name)

            schema = {
                "type": "object",
                "properties": properties,
            }

            if required:
                schema["required"] = required

            return schema
        except Exception:
            # Fallback to generic object
            return {"type": "object"}

    def to_json(self, router: Router, indent: int = 2) -> str:
        """
        Generate OpenAPI schema as JSON string.

        Args:
            router: Router instance
            indent: JSON indentation

        Returns:
            JSON string
        """
        schema = self.generate_schema(router)
        return json.dumps(schema, indent=indent, ensure_ascii=False)


def generate_swagger_ui_html(openapi_url: str = "/openapi.json") -> str:
    """
    Generate Swagger UI HTML.

    Args:
        openapi_url: URL to OpenAPI schema

    Returns:
        HTML string
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{openapi_url}",
                dom_id: "#swagger-ui",
            }});
        }};
    </script>
</body>
</html>"""


def generate_redoc_html(openapi_url: str = "/openapi.json") -> str:
    """
    Generate ReDoc HTML.

    Args:
        openapi_url: URL to OpenAPI schema

    Returns:
        HTML string
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
