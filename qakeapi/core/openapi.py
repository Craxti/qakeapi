import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, create_model


@dataclass
class OpenAPIInfo:
    """OpenAPI information"""

    title: str = "QakeAPI"
    version: str = "1.0.0"
    description: str = ""


@dataclass
class OpenAPIPath:
    """OpenAPI path information"""

    path: str
    method: str
    summary: str = ""
    description: str = ""
    request_model: Optional[BaseModel] = None
    response_model: Optional[BaseModel] = None
    tags: list = field(default_factory=list)


class OpenAPIGenerator:
    """OpenAPI schema generator"""

    def __init__(self, info: OpenAPIInfo):
        self.info = info
        self.paths: Dict[str, Dict[str, Any]] = {}

    def add_path(self, path_info: OpenAPIPath):
        """Add path to OpenAPI schema"""
        if path_info.path not in self.paths:
            self.paths[path_info.path] = {}

        method = path_info.method.lower()

        path_data = {
            "summary": path_info.summary,
            "description": path_info.description,
            "tags": path_info.tags,
            "responses": {
                "200": {
                    "description": "Successful response",
                }
            },
        }

        # Add request body schema if present
        if path_info.request_model:
            path_data["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": path_info.request_model.model_json_schema()
                    }
                }
            }

        # Add response schema if present
        if path_info.response_model:
            path_data["responses"]["200"]["content"] = {
                "application/json": {
                    "schema": path_info.response_model.model_json_schema()
                }
            }

        self.paths[path_info.path][method] = path_data

    def generate(self) -> Dict[str, Any]:
        """Generate OpenAPI schema"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": self.info.title,
                "version": self.info.version,
                "description": self.info.description,
            },
            "paths": self.paths,
        }


def get_swagger_ui_html(openapi_url: str, title: str) -> str:
    """Generate Swagger UI HTML"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="SwaggerUI" />
    <title>{title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *,
        *:before,
        *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin: 0;
            background: #fafafa;
        }}
        #swagger-ui {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" crossorigin></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js" crossorigin></script>
    <script>
        window.onload = () => {{
            const ui = SwaggerUIBundle({{
                url: '{openapi_url}',
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
                docExpansion: 'list',
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                displayRequestDuration: true,
                filter: true,
                tryItOutEnabled: true
            }});
            window.ui = ui;
        }};
    </script>
</body>
</html>
"""
