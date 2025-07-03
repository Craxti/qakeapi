import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum

from pydantic import BaseModel, create_model


class SecuritySchemeType(str, Enum):
    """Security scheme types"""
    HTTP = "http"
    API_KEY = "apiKey"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"


@dataclass
class SecurityScheme:
    """Security scheme definition"""
    type: SecuritySchemeType
    name: str
    description: str = ""
    scheme: str = "bearer"
    bearer_format: Optional[str] = None
    in_: str = "header"
    flows: Optional[Dict[str, Any]] = None


@dataclass
class WebSocketEvent:
    """WebSocket event documentation"""
    name: str
    description: str = ""
    payload_schema: Optional[BaseModel] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WebSocketDocumentation:
    """WebSocket endpoint documentation"""
    path: str
    description: str = ""
    events: List[WebSocketEvent] = field(default_factory=list)
    security: List[Dict[str, List[str]]] = field(default_factory=list)


@dataclass
class OpenAPIInfo:
    """Enhanced OpenAPI information"""
    title: str = "QakeAPI"
    version: str = "1.0.3"
    description: str = ""
    terms_of_service: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    license: Optional[Dict[str, str]] = None
    servers: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class OpenAPIPath:
    """Enhanced OpenAPI path information"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    request_model: Optional[BaseModel] = None
    response_model: Optional[BaseModel] = None
    tags: List[str] = field(default_factory=list)
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    deprecated: bool = False
    operation_id: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class OpenAPIGenerator:
    """Enhanced OpenAPI schema generator with interactive documentation support"""

    def __init__(self, info: OpenAPIInfo):
        self.info = info
        self.paths: Dict[str, Dict[str, Any]] = {}
        self.components: Dict[str, Any] = {
            "schemas": {},
            "securitySchemes": {},
            "examples": {},
            "parameters": {},
            "responses": {}
        }
        self.tags: List[Dict[str, str]] = []
        self.webSocket_docs: List[WebSocketDocumentation] = []
        self.security_schemes: Dict[str, SecurityScheme] = {}

    def add_security_scheme(self, name: str, scheme: SecurityScheme):
        """Add security scheme to OpenAPI schema"""
        self.security_schemes[name] = scheme
        
        scheme_data = {
            "type": scheme.type.value,
            "description": scheme.description
        }
        
        if scheme.type == SecuritySchemeType.HTTP:
            scheme_data["scheme"] = scheme.scheme
            if scheme.bearer_format:
                scheme_data["bearerFormat"] = scheme.bearer_format
        elif scheme.type == SecuritySchemeType.API_KEY:
            scheme_data["name"] = scheme.name
            scheme_data["in"] = scheme.in_
        elif scheme.type in [SecuritySchemeType.OAUTH2, SecuritySchemeType.OPENID_CONNECT]:
            if scheme.flows:
                scheme_data["flows"] = scheme.flows
        
        self.components["securitySchemes"][name] = scheme_data
    
    def add_tag(self, name: str, description: str = ""):
        """Add tag to OpenAPI schema"""
        self.tags.append({"name": name, "description": description})
    
    def add_example(self, name: str, summary: str, description: str, value: Any):
        """Add example to OpenAPI schema"""
        self.components["examples"][name] = {
            "summary": summary,
            "description": description,
            "value": value
        }
    
    def add_parameter(self, name: str, parameter_data: Dict[str, Any]):
        """Add reusable parameter to OpenAPI schema"""
        self.components["parameters"][name] = parameter_data
    
    def add_response(self, name: str, response_data: Dict[str, Any]):
        """Add reusable response to OpenAPI schema"""
        self.components["responses"][name] = response_data
    
    def add_path(self, path_info: OpenAPIPath):
        """Add enhanced path to OpenAPI schema"""
        if path_info.path not in self.paths:
            self.paths[path_info.path] = {}

        method = path_info.method.lower()

        path_data = {
            "summary": path_info.summary,
            "description": path_info.description,
            "tags": path_info.tags,
            "deprecated": path_info.deprecated,
            "parameters": path_info.parameters,
            "responses": path_info.responses or {
                "200": {
                    "description": "Successful response",
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {"type": "string"},
                                    "errors": {"type": "array", "items": {"type": "object"}}
                                }
                            }
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        if path_info.operation_id:
            path_data["operationId"] = path_info.operation_id
        
        if path_info.security:
            path_data["security"] = path_info.security

        # Add request body schema if present
        if path_info.request_model:
            path_data["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": path_info.request_model.model_json_schema(),
                        "examples": path_info.examples if path_info.examples else {}
                    }
                }
            }

        # Add response schema if present
        if path_info.response_model:
            if "200" in path_data["responses"]:
                path_data["responses"]["200"]["content"] = {
                    "application/json": {
                        "schema": path_info.response_model.model_json_schema()
                    }
                }

        self.paths[path_info.path][method] = path_data
    
    def add_webSocket_documentation(self, ws_doc: WebSocketDocumentation):
        """Add WebSocket documentation"""
        self.webSocket_docs.append(ws_doc)

    def generate(self) -> Dict[str, Any]:
        """Generate enhanced OpenAPI schema"""
        schema = {
            "openapi": "3.1.0",
            "info": {
                "title": self.info.title,
                "version": self.info.version,
                "description": self.info.description,
            },
            "paths": self.paths,
            "components": self.components,
            "tags": self.tags,
        }
        
        if self.info.terms_of_service:
            schema["info"]["termsOfService"] = self.info.terms_of_service
        
        if self.info.contact:
            schema["info"]["contact"] = self.info.contact
        
        if self.info.license:
            schema["info"]["license"] = self.info.license
        
        if self.info.servers:
            schema["servers"] = self.info.servers
        
        # Add global security if any schemes are defined
        if self.security_schemes:
            schema["security"] = [{"bearerAuth": []}]
        
        return schema
    
    def generate_webSocket_docs(self) -> Dict[str, Any]:
        """Generate WebSocket documentation"""
        return {
            "webSocket": {
                "endpoints": [
                    {
                        "path": ws.path,
                        "description": ws.description,
                        "security": ws.security,
                        "events": [
                            {
                                "name": event.name,
                                "description": event.description,
                                "payload_schema": event.payload_schema.model_json_schema() if event.payload_schema else None,
                                "examples": event.examples
                            }
                            for event in ws.events
                        ]
                    }
                    for ws in self.webSocket_docs
                ]
            }
        }


def get_swagger_ui_html(
    openapi_url: str, 
    title: str = "API Documentation",
    theme: str = "default",
    custom_css: Optional[str] = None,
    custom_js: Optional[str] = None
) -> str:
    """Generate enhanced Swagger UI HTML with customization options"""
    
    # Theme configurations
    themes = {
        "default": {
            "css": "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css",
            "bundle": "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js",
            "standalone": "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"
        },
        "dark": {
            "css": "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css",
            "bundle": "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js",
            "standalone": "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"
        }
    }
    
    theme_config = themes.get(theme, themes["default"])
    
    custom_styles = ""
    if theme == "dark":
        custom_styles = """
        body { background-color: #1a1a1a !important; color: #ffffff !important; }
        .swagger-ui .topbar { background-color: #2d2d2d !important; }
        .swagger-ui .info .title { color: #ffffff !important; }
        .swagger-ui .info .description { color: #cccccc !important; }
        .swagger-ui .scheme-container { background-color: #2d2d2d !important; }
        .swagger-ui .opblock { background-color: #2d2d2d !important; border-color: #444444 !important; }
        .swagger-ui .opblock .opblock-summary-description { color: #cccccc !important; }
        """
    
    if custom_css:
        custom_styles += custom_css
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="Interactive API Documentation" />
    <title>{title}</title>
    <link rel="stylesheet" href="{theme_config['css']}" />
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
        {custom_styles}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="{theme_config['bundle']}" crossorigin></script>
    <script src="{theme_config['standalone']}" crossorigin></script>
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
                tryItOutEnabled: true,
                requestInterceptor: (request) => {{
                    // Add custom request interceptor if needed
                    return request;
                }},
                responseInterceptor: (response) => {{
                    // Add custom response interceptor if needed
                    return response;
                }}
            }});
            window.ui = ui;
        }};
        {custom_js or ''}
    </script>
</body>
</html>
"""


def get_redoc_html(
    openapi_url: str, 
    title: str = "API Documentation",
    theme: Dict[str, Any] = None
) -> str:
    """Generate ReDoc HTML with customization options"""
    
    default_theme = {
        "colors": {
            "primary": {
                "main": "#32329f"
            }
        },
        "typography": {
            "fontSize": "14px",
            "lineHeight": "1.5em",
            "fontFamily": "Roboto, sans-serif",
            "headings": {
                "fontFamily": "Roboto, sans-serif",
                "fontWeight": "400"
            }
        }
    }
    
    theme_config = theme or default_theme
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="API Documentation" />
    <title>{title}</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap" />
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #fafafa;
        }}
        #redoc {{
            max-width: 1200px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    <div id="redoc"></div>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
    <script>
        Redoc.init('{openapi_url}', {{
            scrollYOffset: 0,
            hideDownloadButton: false,
            hideHostname: false,
            hideLoading: false,
            nativeScrollbars: false,
            pathInMiddlePanel: false,
            requiredPropsFirst: false,
            sortPropsAlphabetically: false,
            showExtensions: false,
            theme: {json.dumps(theme_config)}
        }}, document.getElementById('redoc'));
    </script>
</body>
</html>
"""


def get_webSocket_docs_html(ws_docs: List[WebSocketDocumentation]) -> str:
    """Generate WebSocket documentation HTML"""
    
    ws_html = ""
    for ws in ws_docs:
        events_html = ""
        for event in ws.events:
            examples_html = ""
            if event.examples:
                examples_html = "<h4>Examples:</h4><ul>"
                for i, example in enumerate(event.examples):
                    examples_html += f"<li><strong>Example {i+1}:</strong><pre>{json.dumps(example, indent=2)}</pre></li>"
                examples_html += "</ul>"
            
            events_html += f"""
            <div class="event">
                <h3>{event.name}</h3>
                <p>{event.description}</p>
                {examples_html}
            </div>
            """
        
        ws_html += f"""
        <div class="websocket-endpoint">
            <h2>WebSocket: {ws.path}</h2>
            <p>{ws.description}</p>
            <div class="events">
                {events_html}
            </div>
        </div>
        """
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>WebSocket Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }}
        .websocket-endpoint {{
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
        }}
        .websocket-endpoint h2 {{
            color: #007acc;
            margin-top: 0;
        }}
        .event {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #007acc;
            border-radius: 4px;
        }}
        .event h3 {{
            margin-top: 0;
            color: #333;
        }}
        pre {{
            background-color: #f1f3f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>WebSocket Documentation</h1>
        {ws_html}
    </div>
</body>
</html>
"""
