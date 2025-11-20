"""
Template system for QakeAPI with Jinja2 integration.
"""

from .jinja2 import Jinja2TemplateEngine, TemplateEngine, render_template, render_template_string
from .live_reload import (
    LiveReloadManager, 
    LiveReloadMiddleware, 
    setup_live_reload, 
    start_live_reload, 
    stop_live_reload,
    add_live_reload_callback,
    remove_live_reload_callback,
    get_live_reload_manager
)

__all__ = [
    "Jinja2TemplateEngine", 
    "TemplateEngine",
    "render_template",
    "render_template_string",
    "LiveReloadManager",
    "LiveReloadMiddleware",
    "setup_live_reload",
    "start_live_reload",
    "stop_live_reload",
    "add_live_reload_callback",
    "remove_live_reload_callback",
    "get_live_reload_manager"
] 