#!/usr/bin/env python3
"""
Live Reload Example Application for QakeAPI.

This example demonstrates automatic template reloading during development.
Features:
- Live reload for HTML templates
- File system watching
- Automatic browser refresh
- Development-friendly template editing

Usage:
    python3 live_reload_app.py

Requirements:
    pip install watchdog
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from qakeapi import Application as QakeAPI, Request, Response
from qakeapi.templates import (
    Jinja2TemplateEngine, 
    render_template, 
    setup_live_reload,
    start_live_reload
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create application
app = QakeAPI("Live Reload Example", version="1.0.3")

# Create templates directory
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

# Initialize template engine with live reload
template_engine = Jinja2TemplateEngine(
    template_dir=str(templates_dir),
    auto_reload=True,
    live_reload=True
)

# Add live reload middleware
@app.middleware()
class LiveReloadMiddleware:
    """Live reload middleware for template changes"""
    
    def __init__(self, enabled: bool = True, port: int = 35729):
        self.enabled = enabled
        self.port = port
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """Inject live reload script into HTML responses"""
        if not self.enabled:
            return response
        
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            # Inject live reload script
            live_reload_script = f"""
<script>
    (function() {{
        var script = document.createElement('script');
        script.src = 'http://localhost:{self.port}/livereload.js';
        document.head.appendChild(script);
    }})();
</script>
"""
            # Add script before closing body tag
            body = response.body.decode()
            if "</body>" in body:
                body = body.replace("</body>", f"{live_reload_script}</body>")
            else:
                body += live_reload_script
            
            response.body = body.encode()
        
        return response

# Create sample templates
def create_sample_templates():
    """Create sample HTML templates for demonstration."""
    
    # Base template
    base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Live Reload Demo{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #007bff; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .content { line-height: 1.6; }
        .feature { background: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .highlight { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 QakeAPI Live Reload Demo</h1>
            <p>Version {{ version }} - Template: {{ template_name }}</p>
        </div>
        
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        
        <div class="footer">
            <p>🔄 Live reload is active! Try editing the template files and watch the browser refresh automatically.</p>
            <p>Current time: {{ current_time }}</p>
        </div>
    </div>
</body>
</html>"""
    
    # Home page template
    home_template = """{% extends "base.html" %}

{% block title %}Home - Live Reload Demo{% endblock %}

{% block content %}
    <h2>Welcome to Live Reload Demo!</h2>
    
    <div class="highlight">
        <strong>✨ Live Reload Features:</strong>
        <ul>
            <li>Automatic template reloading</li>
            <li>File system watching</li>
            <li>Browser auto-refresh</li>
            <li>Development-friendly workflow</li>
        </ul>
    </div>
    
    <div class="feature">
        <h3>How to Test Live Reload:</h3>
        <ol>
            <li>Open this page in your browser</li>
            <li>Edit any template file in the <code>templates/</code> directory</li>
            <li>Save the file</li>
            <li>Watch the browser refresh automatically!</li>
        </ol>
    </div>
    
    <div class="feature">
        <h3>Available Routes:</h3>
        <ul>
            <li><a href="/">Home</a> - This page</li>
            <li><a href="/about">About</a> - About page</li>
            <li><a href="/dynamic">Dynamic</a> - Dynamic content page</li>
            <li><a href="/api/info">API Info</a> - JSON API endpoint</li>
        </ul>
    </div>
    
    <div class="code">
        <strong>Template Variables:</strong><br>
        Version: {{ version }}<br>
        Template: {{ template_name }}<br>
        Current Time: {{ current_time }}<br>
        Counter: {{ counter }}
    </div>
{% endblock %}"""
    
    # About page template
    about_template = """{% extends "base.html" %}

{% block title %}About - Live Reload Demo{% endblock %}

{% block content %}
    <h2>About Live Reload</h2>
    
    <div class="feature">
        <h3>What is Live Reload?</h3>
        <p>Live reload is a development feature that automatically refreshes the browser when template files are modified. This eliminates the need to manually refresh the page during development.</p>
    </div>
    
    <div class="feature">
        <h3>How it Works:</h3>
        <ol>
            <li>The application watches template directories for file changes</li>
            <li>When a change is detected, it triggers a reload</li>
            <li>The browser automatically refreshes to show the updated content</li>
        </ol>
    </div>
    
    <div class="highlight">
        <strong>Benefits:</strong>
        <ul>
            <li>Faster development workflow</li>
            <li>No manual browser refresh needed</li>
            <li>Immediate visual feedback</li>
            <li>Better developer experience</li>
        </ul>
    </div>
    
    <div class="code">
        <strong>Technical Details:</strong><br>
        - Uses watchdog library for file system monitoring<br>
        - Supports multiple template directories<br>
        - Debounced file change detection<br>
        - WebSocket-based browser communication
    </div>
{% endblock %}"""
    
    # Dynamic page template
    dynamic_template = """{% extends "base.html" %}

{% block title %}Dynamic Content - Live Reload Demo{% endblock %}

{% block content %}
    <h2>Dynamic Content Demo</h2>
    
    <div class="feature">
        <h3>Dynamic Data:</h3>
        <p>This page demonstrates dynamic content rendering with live reload.</p>
    </div>
    
    <div class="highlight">
        <h3>User Information:</h3>
        <ul>
            <li><strong>Name:</strong> {{ user.name }}</li>
            <li><strong>Email:</strong> {{ user.email }}</li>
            <li><strong>Role:</strong> {{ user.role }}</li>
            <li><strong>Active:</strong> {{ "Yes" if user.active else "No" }}</li>
        </ul>
    </div>
    
    <div class="feature">
        <h3>Items List:</h3>
        {% if items %}
            <ul>
            {% for item in items %}
                <li>{{ item.name }} - {{ item.description }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No items available.</p>
        {% endif %}
    </div>
    
    <div class="code">
        <strong>Page Statistics:</strong><br>
        Total Items: {{ items|length }}<br>
        User Status: {{ "Active" if user.active else "Inactive" }}<br>
        Template Rendered: {{ current_time }}
    </div>
{% endblock %}"""
    
    # Write templates to files
    templates = {
        "base.html": base_template,
        "home.html": home_template,
        "about.html": about_template,
        "dynamic.html": dynamic_template
    }
    
    for filename, content in templates.items():
        template_path = templates_dir / filename
        template_path.write_text(content)
        logger.info(f"Created template: {template_path}")


# Routes
@app.get("/")
async def home(request) -> Dict[str, Any]:
    """Home page with live reload demonstration."""
    import datetime
    
    context = {
        "version": "1.0.3",
        "template_name": "home.html",
        "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counter": 42
    }
    
    return render_template("home.html", context, template_engine=template_engine)


@app.get("/about")
async def about(request) -> Dict[str, Any]:
    """About page explaining live reload functionality."""
    import datetime
    
    context = {
        "version": "1.0.3",
        "template_name": "about.html",
        "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counter": 0
    }
    
    return render_template("about.html", context, template_engine=template_engine)


@app.get("/dynamic")
async def dynamic(request) -> Dict[str, Any]:
    """Dynamic content page with user data and items."""
    import datetime
    
    # Simulate dynamic data
    user = {
        "name": "John Doe",
        "email": "john@example.com",
        "role": "Developer",
        "active": True
    }
    
    items = [
        {"name": "Item 1", "description": "First dynamic item"},
        {"name": "Item 2", "description": "Second dynamic item"},
        {"name": "Item 3", "description": "Third dynamic item"}
    ]
    
    context = {
        "version": "1.0.3",
        "template_name": "dynamic.html",
        "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "items": items
    }
    
    return render_template("dynamic.html", context, template_engine=template_engine)


@app.get("/api/info")
async def api_info(request) -> Dict[str, Any]:
    """API endpoint returning application information."""
    return {
        "name": "Live Reload Demo",
        "version": "1.0.3",
        "features": [
            "Template live reload",
            "File system watching",
            "Automatic browser refresh",
            "Development workflow optimization"
        ],
        "template_dirs": [str(templates_dir)],
        "live_reload_enabled": template_engine.live_reload_enabled
    }


@app.get("/health")
async def health(request) -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "live_reload_app",
        "version": "1.0.3",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Create templates
    create_sample_templates()
    
    # Start live reload server
    start_live_reload()
    
    # Run application
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8019) 