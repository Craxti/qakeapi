"""
OpenAPI/Swagger documentation generator.

This module provides automatic generation of OpenAPI 3.0 specification
and Swagger UI documentation.
"""

import json
from typing import Any, Dict, List, Optional, get_origin, get_args, Union
from inspect import signature, Parameter

# Swagger UI HTML template
SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{title} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
        .swagger-ui .topbar {{
            display: none;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const specUrl = window.location.origin + "/openapi.json";
            console.log("Loading OpenAPI spec from:", specUrl);
            
            const ui = SwaggerUIBundle({{
                url: specUrl,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                tryItOutEnabled: true,
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                requestInterceptor: function(request) {{
                    // Ensure proper headers for CORS
                    if (!request.headers) {{
                        request.headers = {{}};
                    }}
                    request.headers['Accept'] = 'application/json';
                    request.headers['Content-Type'] = 'application/json';
                    console.log('Request:', request.method, request.url);
                    return request;
                }},
                responseInterceptor: function(response) {{
                    console.log('Response:', response.status, response.url);
                    return response;
                }},
                onComplete: function() {{
                    console.log("Swagger UI loaded successfully");
                }},
                onFailure: function(data) {{
                    console.error("Failed to load Swagger UI:", data);
                    console.error("Error details:", JSON.stringify(data, null, 2));
                }}
            }});
            
            window.ui = ui;
        }};
    </script>
</body>
</html>
"""


class OpenAPIGenerator:
    """OpenAPI 3.0 specification generator."""
    
    def __init__(
        self,
        title: str = "QakeAPI",
        version: str = "1.2.0",
        description: str = "",
    ):
        """
        Initialize OpenAPI generator.
        
        Args:
            title: API title
            version: API version
            description: API description
        """
        self.title = title
        self.version = version
        self.description = description
        self.routes: List[Dict[str, Any]] = []
    
    def add_route(
        self,
        path: str,
        method: str,
        handler: Any,
        summary: str = None,
        description: str = None,
    ) -> None:
        """
        Add route to OpenAPI spec.
        
        Args:
            path: Route path
            method: HTTP method
            handler: Handler function
            summary: Route summary
            description: Route description
        """
        import inspect
        
        # Get handler signature
        sig = inspect.signature(handler)
        
        # Extract parameters
        parameters = []
        request_body = None
        
        for param_name, param in sig.parameters.items():
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            
            # Path parameters
            if "{" + param_name + "}" in path:
                schema = self._get_type_schema(param_type)
                param_spec = {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": schema,
                }
                parameters.append(param_spec)
            
            # Query parameters (skip path params and Request object)
            # Parameters with default values are optional query params
            elif (
                param_name != "request"
                and "{" + param_name + "}" not in path
                and param.default != inspect.Parameter.empty
            ):
                schema = self._get_type_schema(param_type)
                param_spec = {
                    "name": param_name,
                    "in": "query",
                    "required": False,
                    "schema": schema,
                    "description": f"Query parameter {param_name}",
                }
                parameters.append(param_spec)
            # Query parameters without default (for GET requests) - required query params
            elif (
                method == "GET"
                and param_name != "request"
                and "{" + param_name + "}" not in path
                and param.default == inspect.Parameter.empty
                and param.annotation != inspect.Parameter.empty
            ):
                schema = self._get_type_schema(param_type)
                param_spec = {
                    "name": param_name,
                    "in": "query",
                    "required": True,
                    "schema": schema,
                    "description": f"Query parameter {param_name}",
                }
                parameters.append(param_spec)
            
            # Request body (for POST, PUT, PATCH) - skip path params, query params, and Request object
            elif (
                method in ["POST", "PUT", "PATCH"]
                and param_name != "request"
                and param.default == inspect.Parameter.empty
                and "{" + param_name + "}" not in path
            ):
                # Check if it's a BaseModel-like class
                if inspect.isclass(param_type):
                    model_schema = self._get_model_schema(param_type)
                    request_body = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    **model_schema
                                }
                            }
                        }
                    }
                # Or dict type
                elif param_type == dict or param_type == "dict":
                    request_body = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                }
                            }
                        }
                    }
        
        # If POST/PUT/PATCH but no request body detected, add generic one
        if method in ["POST", "PUT", "PATCH"] and not request_body:
            # Check if handler has 'request' parameter (common pattern)
            has_request_param = any(
                param_name == "request" or 
                (param.annotation != inspect.Parameter.empty and inspect.isclass(param.annotation) and 
                 (param.annotation.__name__ == "Request" or "Request" in str(param.annotation)))
                for param_name, param in sig.parameters.items()
            )
            if has_request_param:
                # Add generic request body for handlers with 'request' parameter
                request_body = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            else:
                # Even if no request param, POST/PUT/PATCH usually need body
                request_body = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
        
        # Create operation
        operation = {
            "summary": summary or (handler.__name__ if hasattr(handler, "__name__") else "Operation"),
            "description": description or (handler.__doc__ if hasattr(handler, "__doc__") else ""),
            "operationId": handler.__name__ if hasattr(handler, "__name__") else f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}",
            "tags": self._get_tags(path),
        }
        
        if parameters:
            operation["parameters"] = parameters
        
        if request_body:
            operation["requestBody"] = request_body
        
        # Response schema
        operation["responses"] = {
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            },
            "400": {
                "description": "Bad Request",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            },
            "500": {
                "description": "Internal Server Error",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            }
        }
        
        self.routes.append({
            "path": path,
            "method": method.lower(),
            "operation": operation,
        })
    
    def generate_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification."""
        paths = {}
        
        # Group routes by path
        for route in self.routes:
            path = route["path"]
            method = route["method"]
            operation = route["operation"]
            
            if path not in paths:
                paths[path] = {}
            
            paths[path][method] = operation
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server",
                }
            ],
            "paths": paths,
        }
        
        return spec
    
    def _get_type_name(self, type_hint: Any) -> Any:
        """
        Get OpenAPI type schema from Python type.
        
        Supports:
        - Basic types: int, float, bool, str
        - Complex types: Optional, List, Dict, Union
        - Returns string for simple types, dict for complex types
        """
        # Handle string type hints (from forward references)
        if isinstance(type_hint, str):
            # Try to evaluate or return as string type
            if type_hint in ("int", "integer"):
                return "integer"
            elif type_hint in ("float", "number"):
                return "number"
            elif type_hint in ("bool", "boolean"):
                return "boolean"
            elif type_hint in ("list", "array"):
                return {"type": "array", "items": {}}
            elif type_hint in ("dict", "object"):
                return "object"
            else:
                return "string"
        
        # Handle None type
        if type_hint is type(None):
            return None
        
        # Handle generic types using get_origin
        origin = get_origin(type_hint)
        
        # Handle Optional (Union[Type, None])
        if origin is Union:
            args = get_args(type_hint)
            # Optional is Union[Type, None] - extract the actual type
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                # Use first non-None type
                return self._get_type_name(non_none_args[0])
            # If all are None, return None
            return None
        
        # Handle List types
        if origin is list:
            args = get_args(type_hint)
            item_type = args[0] if args else Any
            return {
                "type": "array",
                "items": self._get_type_schema(item_type)
            }
        
        # Handle Dict types
        if origin is dict:
            args = get_args(type_hint)
            if len(args) >= 2:
                # Dict[KeyType, ValueType]
                value_type = args[1]
                return {
                    "type": "object",
                    "additionalProperties": self._get_type_schema(value_type)
                }
            else:
                # Dict without type args
                return {
                    "type": "object",
                    "additionalProperties": {}
                }
        
        # Handle Tuple types
        if origin is tuple:
            args = get_args(type_hint)
            if args:
                # Use first item type
                item_type = args[0]
                return {
                    "type": "array",
                    "items": self._get_type_schema(item_type)
                }
            return {"type": "array"}
        
        # Handle Set types
        if origin is set:
            args = get_args(type_hint)
            item_type = args[0] if args else Any
            return {
                "type": "array",
                "items": self._get_type_schema(item_type),
                "uniqueItems": True
            }
        
        # Handle basic types
        if type_hint == int:
            return "integer"
        elif type_hint == float:
            return "number"
        elif type_hint == bool:
            return "boolean"
        elif type_hint == str:
            return "string"
        elif type_hint == list:
            return {"type": "array", "items": {}}
        elif type_hint == dict:
            return "object"
        elif type_hint == Any:
            return {}
        
        # For unknown types, try to get type name as string
        if hasattr(type_hint, "__name__"):
            return "string"  # Default to string for unknown types
        
        # Default fallback
        return "string"
    
    def _get_type_schema(self, type_hint: Any) -> Dict[str, Any]:
        """
        Get OpenAPI schema dict from Python type.
        
        This is a wrapper around _get_type_name that always returns
        a dict schema for use in OpenAPI specifications.
        """
        result = self._get_type_name(type_hint)
        
        # If result is string, wrap it in dict
        if isinstance(result, str):
            return {"type": result}
        
        # If result is dict, return as is
        if isinstance(result, dict):
            return result
        
        # If result is None, return empty dict (for Optional)
        if result is None:
            return {}
        
        # Default fallback
        return {"type": "string"}
    
    def _get_model_schema(self, model_class: Any) -> Dict[str, Any]:
        """
        Get schema for model class.
        
        Supports dataclasses and classes with __annotations__.
        Handles Optional fields correctly.
        """
        from dataclasses import is_dataclass, fields
        
        properties = {}
        required_fields = []
        
        if is_dataclass(model_class):
            # Handle dataclasses
            for field in fields(model_class):
                field_name = field.name
                field_type = field.type
                
                # Check if field is optional
                origin = get_origin(field_type)
                from dataclasses import MISSING
                is_optional = (
                    origin is Union and 
                    type(None) in get_args(field_type)
                ) or field.default is not MISSING or field.default_factory is not MISSING
                
                # Get schema for field type
                if origin is Union and type(None) in get_args(field_type):
                    # Extract non-None type from Optional
                    args = get_args(field_type)
                    non_none_type = next((arg for arg in args if arg is not type(None)), Any)
                    field_schema = self._get_type_schema(non_none_type)
                else:
                    field_schema = self._get_type_schema(field_type)
                
                properties[field_name] = field_schema
                
                # Add to required if not optional
                if not is_optional:
                    required_fields.append(field_name)
        
        elif hasattr(model_class, "__annotations__"):
            # Handle regular classes with annotations
            for field_name, field_type in model_class.__annotations__.items():
                # Check if Optional
                origin = get_origin(field_type)
                is_optional = origin is Union and type(None) in get_args(field_type)
                
                if is_optional:
                    args = get_args(field_type)
                    non_none_type = next((arg for arg in args if arg is not type(None)), Any)
                    field_schema = self._get_type_schema(non_none_type)
                else:
                    field_schema = self._get_type_schema(field_type)
                
                properties[field_name] = field_schema
                
                if not is_optional:
                    required_fields.append(field_name)
        
        result = {"properties": properties}
        
        # Add required fields if any
        if required_fields:
            result["required"] = required_fields
        
        return result
    
    def _get_tags(self, path: str) -> List[str]:
        """Get tags for path based on path structure."""
        # Extract first path segment as tag
        parts = path.strip("/").split("/")
        if parts and parts[0]:
            # Remove path parameters
            tag = parts[0].replace("{", "").replace("}", "")
            return [tag]
        # Return default tag for root path or empty path
        return ["default"]

