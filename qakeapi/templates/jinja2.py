"""
Jinja2 template engine integration for QakeAPI.
"""
import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from jinja2 import Template as Jinja2Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Jinja2Template = None

from ..core.responses import Response
from .live_reload import setup_live_reload, start_live_reload, stop_live_reload

logger = logging.getLogger(__name__)


class TemplateEngine(ABC):
    """Abstract base class for template engines."""
    
    @abstractmethod
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with given context."""
        pass
    
    @abstractmethod
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render template string with given context."""
        pass


class Jinja2TemplateEngine(TemplateEngine):
    """Jinja2 template engine implementation."""
    
    def __init__(
        self,
        template_dir: Union[str, Path] = "templates",
        auto_reload: bool = True,
        autoescape: bool = True,
        live_reload: bool = False,
        **kwargs
    ):
        """
        Initialize Jinja2 template engine.
        
        Args:
            template_dir: Directory containing templates
            auto_reload: Enable auto-reload for development
            autoescape: Enable auto-escaping for security
            live_reload: Enable live reload functionality
            **kwargs: Additional Jinja2 environment options
        """
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required. Install with: pip install jinja2")
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure Jinja2 environment
        env_kwargs = {
            "loader": FileSystemLoader(str(self.template_dir)),
            "auto_reload": auto_reload,
            "autoescape": select_autoescape() if autoescape else False,
            **kwargs
        }
        
        self.env = Environment(**env_kwargs)
        self.live_reload_enabled = live_reload
        
        # Setup live reload if enabled
        if self.live_reload_enabled:
            try:
                setup_live_reload([str(self.template_dir)], enabled=True)
                start_live_reload()
                logger.info(f"Live reload enabled for template directory: {template_dir}")
            except ImportError:
                logger.warning("Live reload requires watchdog. Install with: pip install watchdog")
                self.live_reload_enabled = False
        
        logger.debug(f"Initialized Jinja2 template engine with template_dir: {template_dir}")
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with given context."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render template string with given context."""
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template string: {e}")
            raise
    
    def add_filter(self, name: str, filter_func: callable) -> None:
        """Add custom filter to Jinja2 environment."""
        self.env.filters[name] = filter_func
        logger.debug(f"Added Jinja2 filter: {name}")
    
    def add_function(self, name: str, func: callable) -> None:
        """Add custom function to Jinja2 environment."""
        self.env.globals[name] = func
        logger.debug(f"Added Jinja2 function: {name}")
    
    def add_global(self, name: str, value: Any) -> None:
        """Add global variable to Jinja2 environment."""
        self.env.globals[name] = value
        logger.debug(f"Added Jinja2 global: {name}")
    
    def get_template(self, template_name: str) -> Jinja2Template:
        """Get Jinja2 template object."""
        return self.env.get_template(template_name)
    
    def stop_live_reload(self):
        """Stop live reload functionality."""
        if self.live_reload_enabled:
            stop_live_reload()
            self.live_reload_enabled = False
            logger.info("Live reload stopped")
    
    def __del__(self):
        """Cleanup when template engine is destroyed."""
        if hasattr(self, 'live_reload_enabled') and self.live_reload_enabled:
            self.stop_live_reload()


def render_template(
    template_name: str,
    context: Dict[str, Any],
    template_engine: Optional[Jinja2TemplateEngine] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    live_reload: bool = False
) -> Response:
    """
    Render template and return Response.
    
    Args:
        template_name: Name of the template file
        context: Template context variables
        template_engine: Template engine instance (creates default if None)
        status_code: HTTP status code
        headers: Additional response headers
        live_reload: Enable live reload for this template
    """
    if template_engine is None:
        template_engine = Jinja2TemplateEngine(live_reload=live_reload)
    
    content = template_engine.render(template_name, context)
    
    response_headers = {
        "content-type": "text/html; charset=utf-8"
    }
    if headers:
        response_headers.update(headers)
    
    return Response(
        content=content,
        status_code=status_code,
        headers=[(k.encode(), v.encode()) for k, v in response_headers.items()]
    )


def render_template_string(
    template_string: str,
    context: Dict[str, Any],
    template_engine: Optional[Jinja2TemplateEngine] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    Render template string and return Response.
    
    Args:
        template_string: Template string content
        context: Template context variables
        template_engine: Template engine instance (creates default if None)
        status_code: HTTP status code
        headers: Additional response headers
    """
    if template_engine is None:
        template_engine = Jinja2TemplateEngine()
    
    content = template_engine.render_string(template_string, context)
    
    response_headers = {
        "content-type": "text/html; charset=utf-8"
    }
    if headers:
        response_headers.update(headers)
    
    return Response(
        content=content,
        status_code=status_code,
        headers=[(k.encode(), v.encode()) for k, v in response_headers.items()]
    ) 