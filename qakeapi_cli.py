#!/usr/bin/env python3
"""
QakeAPI CLI - Command Line Interface for generating QakeAPI projects.

This tool helps you quickly scaffold new QakeAPI applications with
pre-configured structures and common patterns.

Usage:
    python3 qakeapi_cli.py create my-app
    python3 qakeapi_cli.py create my-app --template=api
    python3 qakeapi_cli.py create my-app --template=web --features=auth,cache,websockets
"""

import argparse
import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
import textwrap


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def get_user_input(prompt: str, default: str = "", required: bool = True) -> str:
    """Get user input with validation."""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if not required or user_input:
            return user_input
        print_error("This field is required!")


def get_choice(prompt: str, options: List[str], default: int = 0) -> int:
    """Get user choice from a list of options."""
    print(f"\n{prompt}")
    for i, option in enumerate(options):
        marker = "→" if i == default else " "
        print(f"  {marker} {i+1}. {option}")
    
    while True:
        try:
            choice = input(f"\nSelect option [1-{len(options)}] (default: {default+1}): ").strip()
            if not choice:
                return default
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                return choice_idx
            print_error(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_error("Please enter a valid number")


def get_multiple_choice(prompt: str, options: List[str]) -> Set[str]:
    """Get multiple choices from a list of options."""
    print(f"\n{prompt}")
    for i, option in enumerate(options):
        print(f"  {i+1}. {option}")
    
    print("\nEnter numbers separated by commas (e.g., 1,3,5) or 'all' for all features:")
    
    while True:
        choice = input("Your choice: ").strip().lower()
        
        if choice == "all":
            return set(options)
        
        try:
            selected_indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected_features = set()
            
            for idx in selected_indices:
                if 0 <= idx < len(options):
                    selected_features.add(options[idx])
                else:
                    print_error(f"Invalid option number: {idx + 1}")
                    continue
            
            if selected_features:
                return selected_features
            else:
                print_error("Please select at least one option")
        except ValueError:
            print_error("Please enter valid numbers separated by commas")


class ProjectGenerator:
    """Generator for QakeAPI projects."""
    
    def __init__(self):
        self.templates = {
            "basic": {
                "name": "Basic API",
                "description": "Simple API with basic CRUD operations",
                "features": ["routing", "validation", "docs"]
            },
            "api": {
                "name": "Full API",
                "description": "Complete API with authentication, database, and advanced features",
                "features": ["routing", "validation", "docs", "auth", "database", "cache", "rate_limit"]
            },
            "web": {
                "name": "Web Application",
                "description": "Web application with templates and frontend",
                "features": ["routing", "validation", "templates", "static", "auth", "csrf"]
            },
            "microservice": {
                "name": "Microservice",
                "description": "Lightweight microservice with minimal dependencies",
                "features": ["routing", "validation", "health", "metrics"]
            }
        }
        
        self.available_features = {
            "routing": "HTTP routing with path parameters",
            "validation": "Request/response validation with Pydantic",
            "docs": "OpenAPI/Swagger documentation",
            "auth": "JWT authentication",
            "database": "Database integration (SQLAlchemy)",
            "cache": "Redis caching",
            "rate_limit": "Rate limiting",
            "templates": "Jinja2 template engine",
            "static": "Static file serving",
            "csrf": "CSRF protection",
            "websockets": "WebSocket support",
            "background": "Background task processing",
            "file_upload": "File upload handling",
            "health": "Health check endpoints",
            "metrics": "Application metrics",
            "logging": "Structured logging",
            "testing": "Test suite with pytest",
            "docker": "Docker configuration",
            "live_reload": "Development live reload"
        }
    
    def generate_project(self, project_name: str, template: str = "basic", 
                        features: Optional[Set[str]] = None, 
                        interactive: bool = True) -> bool:
        """Generate a new QakeAPI project."""
        
        if interactive:
            return self._generate_interactive(project_name)
        else:
            return self._generate_from_template(project_name, template, features or set())
    
    def _generate_interactive(self, project_name: str) -> bool:
        """Generate project interactively."""
        print_header("🚀 QakeAPI Project Generator")
        
        # Get project details
        print_info("Let's create your QakeAPI project!")
        
        project_name = get_user_input("Project name", project_name)
        description = get_user_input("Description", "A QakeAPI web application")
        author = get_user_input("Author", "Your Name")
        email = get_user_input("Email", "your.email@example.com")
        version = get_user_input("Version", "1.0.3")
        
        # Select template
        template_options = list(self.templates.keys())
        template_names = [self.templates[t]["name"] for t in template_options]
        template_idx = get_choice("Select project template:", template_names)
        selected_template = template_options[template_idx]
        
        print_info(f"Selected template: {self.templates[selected_template]['name']}")
        print_info(f"Description: {self.templates[selected_template]['description']}")
        
        # Select features
        print_info("\nAvailable features:")
        feature_options = list(self.available_features.keys())
        selected_features = get_multiple_choice(
            "Select features to include:",
            [f"{f} - {self.available_features[f]}" for f in feature_options]
        )
        
        # Extract feature names from descriptions
        selected_features = {f.split(" - ")[0] for f in selected_features}
        
        # Add template default features
        template_features = set(self.templates[selected_template]["features"])
        all_features = selected_features | template_features
        
        print_success(f"Selected {len(all_features)} features")
        
        # Confirm generation
        print_header("📋 Project Summary")
        print(f"Project Name: {project_name}")
        print(f"Description: {description}")
        print(f"Template: {self.templates[selected_template]['name']}")
        print(f"Features: {', '.join(sorted(all_features))}")
        
        confirm = input("\nGenerate project? [Y/n]: ").strip().lower()
        if confirm in ['n', 'no']:
            print_info("Project generation cancelled")
            return False
        
        return self._generate_from_template(project_name, selected_template, all_features, {
            "description": description,
            "version": version,
            "author": author,
            "email": email
        })
    
    def _generate_from_template(self, project_name: str, template: str, 
                               features: Set[str], metadata: Optional[Dict] = None) -> bool:
        """Generate project from template."""
        
        project_path = Path(project_name)
        
        if project_path.exists():
            print_error(f"Directory '{project_name}' already exists!")
            return False
        
        try:
            # Create project structure
            self._create_project_structure(project_path, features)
            
            # Generate files
            self._generate_main_app(project_path, template, features, metadata)
            self._generate_requirements(project_path, features)
            self._generate_config(project_path, features)
            self._generate_readme(project_path, metadata or {})
            
            # Generate feature-specific files
            if "auth" in features:
                self._generate_auth_files(project_path)
            
            if "database" in features:
                self._generate_database_files(project_path)
            
            if "templates" in features:
                self._generate_template_files(project_path)
            
            if "testing" in features:
                self._generate_test_files(project_path)
            
            if "docker" in features:
                self._generate_docker_files(project_path)
            
            print_success(f"Project '{project_name}' generated successfully!")
            print_info(f"Project location: {project_path.absolute()}")
            
            # Show next steps
            self._show_next_steps(project_path, features)
            
            return True
            
        except Exception as e:
            print_error(f"Failed to generate project: {e}")
            if project_path.exists():
                shutil.rmtree(project_path)
            return False
    
    def _create_project_structure(self, project_path: Path, features: Set[str]):
        """Create project directory structure."""
        directories = [
            "",
            "app",
            "app/api",
            "app/core",
            "app/models",
            "app/schemas",
            "app/services",
            "app/utils",
            "tests",
            "docs"
        ]
        
        if "templates" in features:
            directories.extend([
                "templates",
                "static",
                "static/css",
                "static/js",
                "static/images"
            ])
        
        if "database" in features:
            directories.extend([
                "migrations",
                "alembic"
            ])
        
        for directory in directories:
            (project_path / directory).mkdir(parents=True, exist_ok=True)
    
    def _generate_main_app(self, project_path: Path, template: str, 
                          features: Set[str], metadata: Optional[Dict] = None):
        """Generate main application file."""
        app_content = self._get_app_template(template, features, metadata or {})
        
        with open(project_path / "app" / "main.py", "w") as f:
            f.write(app_content)
    
    def _get_app_template(self, template: str, features: Set[str], metadata: Dict) -> str:
        """Get application template content."""
        
        imports = ["from qakeapi import Application, Request, Response"]
        
        if "validation" in features:
            imports.append("from qakeapi.validation.models import validate_request_body, RequestModel")
            imports.append("from pydantic import Field")
        
        if "auth" in features:
            imports.append("from qakeapi.security.jwt_auth import JWTAuth")
        
        if "templates" in features:
            imports.append("from qakeapi.templates import Jinja2TemplateEngine, render_template")
        
        if "database" in features:
            imports.append("from sqlalchemy import create_engine, Column, Integer, String, DateTime")
            imports.append("from sqlalchemy.ext.declarative import declarative_base")
            imports.append("from sqlalchemy.orm import sessionmaker")
        
        if "cache" in features:
            imports.append("from qakeapi.cache import Cache")
        
        if "rate_limit" in features:
            imports.append("from qakeapi.security.rate_limit import RateLimitMiddleware")
        
        imports_str = "\n".join(imports)
        
        # Generate app initialization
        app_init = f"""
# Initialize application
app = Application(
    title="{metadata.get('description', 'QakeAPI Application')}",
    version="{metadata.get('version', '1.0.0')}",
    description="{metadata.get('description', 'A QakeAPI application')}"
)
"""
        
        # Generate feature-specific code
        feature_code = []
        
        if "auth" in features:
            feature_code.append(self._get_auth_code())
        
        if "database" in features:
            feature_code.append(self._get_database_code())
        
        if "templates" in features:
            feature_code.append(self._get_templates_code())
        
        if "cache" in features:
            feature_code.append(self._get_cache_code())
        
        if "rate_limit" in features:
            feature_code.append(self._get_rate_limit_code())
        
        # Generate routes
        routes = self._get_routes_code(features)
        
        # Generate main block
        main_block = """
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""
        
        return f'''#!/usr/bin/env python3
"""
{metadata.get('description', 'QakeAPI Application')}

Author: {metadata.get('author', 'Your Name')}
Email: {metadata.get('email', 'your.email@example.com')}
Version: {metadata.get('version', '1.0.0')}
"""

{imports_str}

{app_init}

{chr(10).join(feature_code)}

{routes}

{main_block}
'''
    
    def _get_auth_code(self) -> str:
        """Get authentication code."""
        return '''
# JWT Authentication
jwt_auth = JWTAuth(secret_key="your-secret-key-here")

@app.middleware()
class AuthMiddleware:
    """Authentication middleware"""
    
    async def process_request(self, request: Request) -> None:
        """Process authentication"""
        # Add authentication logic here
        pass
'''
    
    def _get_database_code(self) -> str:
        """Get database code."""
        return '''
# Database setup
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _get_templates_code(self) -> str:
        """Get templates code."""
        return '''
# Template engine
template_engine = Jinja2TemplateEngine(
    template_dir="templates",
    auto_reload=True
)
'''
    
    def _get_cache_code(self) -> str:
        """Get cache code."""
        return '''
# Cache setup
cache = Cache()
'''
    
    def _get_rate_limit_code(self) -> str:
        """Get rate limit code."""
        return '''
# Rate limiting
@app.middleware()
class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    async def process_request(self, request: Request) -> None:
        """Process rate limiting"""
        # Add rate limiting logic here
        pass
'''
    
    def _get_routes_code(self, features: Set[str]) -> str:
        """Get routes code."""
        routes = []
        
        # Basic routes
        routes.append('''
@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {"message": "QakeAPI application is running"}
''')
        
        if "health" in features:
            routes.append('''
@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
''')
        
        if "docs" in features:
            routes.append('''
@app.get("/docs")
async def docs(request: Request):
    """API documentation"""
    return {"message": "API documentation available at /openapi.json"}
''')
        
        if "templates" in features:
            routes.append('''
@app.get("/page")
async def page(request: Request):
    """Example page with template"""
    context = {
        "title": "Welcome",
        "message": "This is a template page"
    }
    return render_template("index.html", context, template_engine=template_engine)
''')
        
        return "\n".join(routes)
    
    def _generate_requirements(self, project_path: Path, features: Set[str]):
        """Generate requirements.txt file."""
        requirements = [
            "qakeapi>=1.0.3",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0"
        ]
        
        if "database" in features:
            requirements.extend([
                "sqlalchemy>=2.0.0",
                "alembic>=1.12.0"
            ])
        
        if "cache" in features:
            requirements.append("redis>=4.5.0")
        
        if "templates" in features:
            requirements.append("jinja2>=3.1.0")
        
        if "auth" in features:
            requirements.append("python-jose[cryptography]>=3.3.0")
        
        if "testing" in features:
            requirements.extend([
                "pytest>=7.0.0",
                "pytest-asyncio>=0.21.0",
                "httpx>=0.24.0"
            ])
        
        if "docker" in features:
            requirements.append("gunicorn>=21.0.0")
        
        with open(project_path / "requirements.txt", "w") as f:
            f.write("\n".join(requirements))
    
    def _generate_config(self, project_path: Path, features: Set[str]):
        """Generate configuration file."""
        config_content = '''# Application configuration
APP_NAME = "QakeAPI Application"
APP_VERSION = "1.0.0"
DEBUG = True

# Server configuration
HOST = "127.0.0.1"
PORT = 8000

# Security
SECRET_KEY = "your-secret-key-here-change-in-production"
'''
        
        if "database" in features:
            config_content += '''
# Database
DATABASE_URL = "sqlite:///./app.db"
'''
        
        if "cache" in features:
            config_content += '''
# Cache
REDIS_URL = "redis://localhost:6379"
'''
        
        with open(project_path / "app" / "config.py", "w") as f:
            f.write(config_content)
    
    def _generate_readme(self, project_path: Path, metadata: Dict):
        """Generate README.md file."""
        readme_content = f'''# {metadata.get('description', 'QakeAPI Application')}

A QakeAPI application with modern web development features.

## Features

- Fast async web framework
- Request/response validation
- OpenAPI documentation
- And more...

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python app/main.py
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload
```

## Development

- API documentation: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
'''
        
        with open(project_path / "README.md", "w") as f:
            f.write(readme_content)
    
    def _generate_auth_files(self, project_path: Path):
        """Generate authentication-related files."""
        auth_content = '''from qakeapi.security.jwt_auth import JWTAuth
from datetime import datetime, timedelta

# JWT configuration
jwt_auth = JWTAuth(
    secret_key="your-secret-key-here",
    algorithm="HS256",
    access_token_expire_minutes=30
)

def create_access_token(data: dict):
    """Create access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt_auth.create_access_token(to_encode)

def verify_token(token: str):
    """Verify JWT token"""
    return jwt_auth.verify_token(token)
'''
        
        with open(project_path / "app" / "auth.py", "w") as f:
            f.write(auth_content)
    
    def _generate_database_files(self, project_path: Path):
        """Generate database-related files."""
        models_content = '''from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
'''
        
        with open(project_path / "app" / "models.py", "w") as f:
            f.write(models_content)
    
    def _generate_template_files(self, project_path: Path):
        """Generate template files."""
        base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/docs">API Docs</a>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2024 QakeAPI Application</p>
    </footer>
</body>
</html>'''
        
        index_template = '''{% extends "base.html" %}

{% block title %}Welcome{% endblock %}

{% block content %}
<div class="container">
    <h1>Welcome to QakeAPI</h1>
    <p>This is your new QakeAPI application.</p>
    <p>Message: {{ message }}</p>
</div>
{% endblock %}'''
        
        with open(project_path / "templates" / "base.html", "w") as f:
            f.write(base_template)
        
        with open(project_path / "templates" / "index.html", "w") as f:
            f.write(index_template)
        
        # Create basic CSS
        css_content = '''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: #333;
    color: white;
    padding: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    margin-right: 1rem;
}

nav a:hover {
    text-decoration: underline;
}

footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 1rem;
    position: fixed;
    bottom: 0;
    width: 100%;
}'''
        
        with open(project_path / "static" / "css" / "style.css", "w") as f:
            f.write(css_content)
    
    def _generate_test_files(self, project_path: Path):
        """Generate test files."""
        test_content = '''import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_root():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

@pytest.mark.asyncio
async def test_health():
    """Test health endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
'''
        
        with open(project_path / "tests" / "test_main.py", "w") as f:
            f.write(test_content)
        
        # Create pytest config
        pytest_ini = '''[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
'''
        
        with open(project_path / "pytest.ini", "w") as f:
            f.write(pytest_ini)
    
    def _generate_docker_files(self, project_path: Path):
        """Generate Docker files."""
        dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        
        docker_compose = '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
    volumes:
      - .:/app
    depends_on:
      - redis
      - db

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: qakeapi
      POSTGRES_USER: qakeapi
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
'''
        
        with open(project_path / "Dockerfile", "w") as f:
            f.write(dockerfile)
        
        with open(project_path / "docker-compose.yml", "w") as f:
            f.write(docker_compose)
    
    def _show_next_steps(self, project_path: Path, features: Set[str]):
        """Show next steps after project generation."""
        print_header("🎉 Project Generated Successfully!")
        
        print_info("Next steps:")
        print("1. Navigate to your project:")
        print(f"   cd {project_path.name}")
        
        print("2. Create virtual environment:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        
        print("3. Install dependencies:")
        print("   pip install -r requirements.txt")
        
        print("4. Run the application:")
        print("   python app/main.py")
        
        if "docker" in features:
            print("\n5. Or run with Docker:")
            print("   docker-compose up --build")
        
        print("\n6. Open in browser:")
        print("   http://localhost:8000")
        
        if "docs" in features:
            print("   http://localhost:8000/docs")
        
        print("\nHappy coding! 🚀")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="QakeAPI CLI - Generate new QakeAPI projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
Examples:
  python3 qakeapi_cli.py create my-app
  python3 qakeapi_cli.py create my-api --template=api
  python3 qakeapi_cli.py create my-web --template=web --features=auth,templates
        ''')
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--template", choices=["basic", "api", "web", "microservice"],
                              default="basic", help="Project template")
    create_parser.add_argument("--features", help="Comma-separated list of features")
    create_parser.add_argument("--no-interactive", action="store_true",
                              help="Skip interactive questions")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available templates and features")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    generator = ProjectGenerator()
    
    if args.command == "create":
        features = set()
        if args.features:
            features = set(args.features.split(","))
        
        success = generator.generate_project(
            args.name,
            template=args.template,
            features=features,
            interactive=not args.no_interactive
        )
        
        if not success:
            sys.exit(1)
    
    elif args.command == "list":
        print_header("📋 Available Templates")
        for key, template in generator.templates.items():
            print(f"{Colors.BOLD}{key}{Colors.ENDC}: {template['name']}")
            print(f"  {template['description']}")
            print(f"  Features: {', '.join(template['features'])}")
            print()
        
        print_header("🔧 Available Features")
        for feature, description in generator.available_features.items():
            print(f"{Colors.BOLD}{feature}{Colors.ENDC}: {description}")


if __name__ == "__main__":
    main() 