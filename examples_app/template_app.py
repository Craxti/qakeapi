"""
Example application demonstrating Jinja2 template usage.
"""
import os
import tempfile
from pathlib import Path

from qakeapi import Application
from qakeapi.templates.jinja2 import Jinja2TemplateEngine, render_template_string
from qakeapi.templates.renderers import create_template_engine, render_template

# Create a temporary directory for templates
temp_dir = Path(tempfile.mkdtemp())
templates_dir = temp_dir / "templates"
templates_dir.mkdir(exist_ok=True)

# Create test templates
base_template = templates_dir / "base.html"
base_template.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .content { margin: 20px 0; }
        .footer { background: #f0f0f0; padding: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{% block header %}{% endblock %}</h1>
        </div>
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        <div class="footer">
            {% block footer %}QakeAPI Template Example{% endblock %}
        </div>
    </div>
</body>
</html>
""")

index_template = templates_dir / "index.html"
index_template.write_text("""
{% extends "base.html" %}

{% block title %}Home Page{% endblock %}

{% block header %}Welcome to QakeAPI{% endblock %}

{% block content %}
    <h2>Hello, {{ name }}!</h2>
    <p>This is an example of using Jinja2 templates in QakeAPI.</p>
    
    <h3>User List:</h3>
    <ul>
    {% for user in users %}
        <li>{{ user.name }} ({{ user.email }})</li>
    {% endfor %}
    </ul>
    
    <h3>Statistics:</h3>
    <p>Total users: {{ users|length }}</p>
    <p>Time: {{ current_time }}</p>
{% endblock %}
""")

user_template = templates_dir / "user.html"
user_template.write_text("""
{% extends "base.html" %}

{% block title %}User Profile{% endblock %}

{% block header %}Profile: {{ user.name }}{% endblock %}

{% block content %}
    <div class="user-profile">
        <h2>{{ user.name }}</h2>
        <p><strong>Email:</strong> {{ user.email }}</p>
        <p><strong>Age:</strong> {{ user.age }}</p>
        <p><strong>Role:</strong> {{ user.role }}</p>
        
        {% if user.bio %}
            <h3>About:</h3>
            <p>{{ user.bio }}</p>
        {% endif %}
        
        <h3>Skills:</h3>
        <ul>
        {% for skill in user.skills %}
            <li>{{ skill }}</li>
        {% endfor %}
        </ul>
    </div>
{% endblock %}
""")

# Create application
app = Application(title="Template Example", version="1.0.3")

# Create template engine with caching (debug disabled to avoid recursion)
template_engine = create_template_engine(
    template_dir=str(templates_dir),
    enable_cache=True,
    enable_debug=False
)

# Add custom filters
def format_date(value):
    """Format date."""
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d %H:%M')
    return str(value)

def truncate_text(value, length=50):
    """Truncate text."""
    if len(value) <= length:
        return value
    return value[:length] + "..."

template_engine.add_filter("format_date", format_date)
template_engine.add_filter("truncate", truncate_text)

# Add custom functions
def get_user_count():
    """Get user count."""
    return len(users_data)

template_engine.add_function("get_user_count", get_user_count)

# Test data
users_data = [
    {
        "id": 1,
        "name": "Ivan Petrov",
        "email": "ivan@example.com",
        "age": 25,
        "role": "Developer",
        "bio": "Experienced Python developer with 5 years of experience.",
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL"]
    },
    {
        "id": 2,
        "name": "Maria Sidorova",
        "email": "maria@example.com",
        "age": 28,
        "role": "Designer",
        "bio": "UI/UX designer specializing in web interfaces.",
        "skills": ["Figma", "Adobe XD", "HTML", "CSS", "JavaScript"]
    },
    {
        "id": 3,
        "name": "Alexey Kozlov",
        "email": "alex@example.com",
        "age": 30,
        "role": "Project Manager",
        "bio": "Experienced project manager in the IT field.",
        "skills": ["Agile", "Scrum", "Jira", "Confluence"]
    }
]

from datetime import datetime

@app.get("/")
async def index(request):
    """Home page using template."""
    context = {
        "name": "User",
        "users": users_data,
        "current_time": datetime.now()
    }
    
    return render_template(
        "index.html",
        context,
        template_engine=template_engine
    )

@app.get("/user/{user_id}")
async def user_profile(request):
    """User profile page."""
    # Extract user_id from path parameters
    user_id = int(request.path_params.get("user_id", 0))
    
    user = next((u for u in users_data if u["id"] == user_id), None)
    
    if not user:
        return {"error": "User not found"}, 404
    
    context = {
        "user": user,
        "current_time": datetime.now()
    }
    
    return render_template(
        "user.html",
        context,
        template_engine=template_engine
    )

@app.get("/string")
async def render_string_example(request):
    """Example of rendering a template string."""
    template_string = """
    <h1>Rendering template string</h1>
    <p>Hello, {{ name }}!</p>
    <p>Current time: {{ time | format_date }}</p>
    <p>User count: {{ get_user_count() }}</p>
    """
    
    context = {
        "name": "Guest",
        "time": datetime.now()
    }
    
    return render_template_string(
        template_string,
        context,
        template_engine=template_engine
    )

@app.get("/debug")
async def template_debug_info(request):
    """Template debugging information."""
    if hasattr(template_engine, 'debugger'):
        stats = template_engine.debugger.get_stats()
        return {
            "template_stats": stats,
            "cache_enabled": hasattr(template_engine, 'cache'),
            "cache_size": len(template_engine.cache._cache) if hasattr(template_engine, 'cache') else 0
        }
    return {"error": "Debugging not enabled"}

@app.get("/cache/clear")
async def clear_cache(request):
    """Clear template cache."""
    if hasattr(template_engine, 'cache'):
        template_engine.cache.clear()
        return {"message": "Cache cleared"}
    return {"error": "Caching not enabled"}

@app.get("/users")
async def users_list(request):
    """List of users in JSON format."""
    return {"users": users_data}

if __name__ == "__main__":
    import uvicorn
    print(f"Templates created in: {templates_dir}")
    print("Available endpoints:")
    print("  GET / - Home page")
    print("  GET /user/{id} - User profile")
    print("  GET /string - Rendering string")
    print("  GET /debug - Template debugging information")
    print("  GET /cache/clear - Clear cache")
    print("  GET /users - List of users (JSON)")
    
    uvicorn.run("template_app:app", host="0.0.0.0", port=8025, reload=False) 