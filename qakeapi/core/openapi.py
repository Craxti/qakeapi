from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, create_model
import json

class OpenAPIInfo:
    def __init__(
        self,
        title: str = "API Documentation",
        version: str = "1.0.0",
        description: str = ""
    ):
        self.title = title
        self.version = version
        self.description = description

class OpenAPIPath:
    def __init__(
        self,
        path: str,
        method: str,
        summary: str = "",
        description: str = "",
        request_model: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
        tags: List[str] = None,
        deprecated: bool = False
    ):
        self.path = path
        self.method = method.lower()
        self.summary = summary
        self.description = description
        self.request_model = request_model
        self.response_model = response_model
        self.tags = tags or []
        self.deprecated = deprecated

class OpenAPIGenerator:
    def __init__(self, info: OpenAPIInfo):
        self.info = info
        self.paths: Dict[str, Dict[str, OpenAPIPath]] = {}
        
    def add_path(self, path_info: OpenAPIPath) -> None:
        if path_info.path not in self.paths:
            self.paths[path_info.path] = {}
        self.paths[path_info.path][path_info.method] = path_info
        
    def _schema_from_model(self, model: Type[BaseModel]) -> Dict[str, Any]:
        return model.model_json_schema()
        
    def _path_to_openapi(self, path: str) -> str:
        """Convert path parameters from {param} to {param}"""
        return path
        
    def generate(self) -> Dict[str, Any]:
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": self.info.title,
                "version": self.info.version,
                "description": self.info.description
            },
            "paths": {}
        }
        
        # Добавляем пути
        for path, methods in self.paths.items():
            openapi_path = self._path_to_openapi(path)
            openapi["paths"][openapi_path] = {}
            
            for method, path_info in methods.items():
                method_info = {
                    "summary": path_info.summary,
                    "description": path_info.description,
                    "tags": path_info.tags,
                    "deprecated": path_info.deprecated,
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {}
                            }
                        }
                    }
                }
                
                # Добавляем схему запроса
                if path_info.request_model:
                    method_info["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": self._schema_from_model(path_info.request_model)
                            }
                        }
                    }
                    
                # Добавляем схему ответа
                if path_info.response_model:
                    method_info["responses"]["200"]["content"]["application/json"]["schema"] = \
                        self._schema_from_model(path_info.response_model)
                        
                openapi["paths"][openapi_path][method] = method_info
                
        return openapi

def get_swagger_ui_html(
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="{swagger_css_url}">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="{swagger_js_url}"></script>
    <script>
        window.onload = function() {{
            window.ui = SwaggerUIBundle({{
                url: "{openapi_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            }});
        }}
    </script>
</body>
</html>
""" 