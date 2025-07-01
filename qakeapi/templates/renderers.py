"""
Template renderers and utilities for QakeAPI.
"""
import logging
import time
from functools import wraps
from typing import Any, Dict, Optional, Callable

from .jinja2 import Jinja2TemplateEngine, render_template, render_template_string

logger = logging.getLogger(__name__)


class TemplateCache:
    """Simple template caching implementation."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get template from cache."""
        if key in self._cache:
            self._access_times[key] = time.time()
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set template in cache."""
        if len(self._cache) >= self.max_size:
            # Remove least recently used
            oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            del self._cache[oldest_key]
            del self._access_times[oldest_key]
        
        self._cache[key] = value
        self._access_times[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cached templates."""
        self._cache.clear()
        self._access_times.clear()


class CachedTemplateEngine(Jinja2TemplateEngine):
    """Jinja2 template engine with caching support."""
    
    def __init__(self, *args, enable_cache: bool = True, cache_size: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_cache = enable_cache
        self.cache = TemplateCache(cache_size) if enable_cache else None
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with caching."""
        if not self.enable_cache or not self.cache:
            return super().render(template_name, context)
        
        # Create cache key from template name and context
        cache_key = f"{template_name}:{hash(str(sorted(context.items())))}"
        
        # Try to get from cache
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Template cache hit: {template_name}")
            return cached_result
        
        # Render and cache
        result = super().render(template_name, context)
        self.cache.set(cache_key, result)
        logger.debug(f"Template cache miss: {template_name}")
        
        return result


def template_debug(func: Callable) -> Callable:
    """Decorator for debugging template rendering."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            logger.debug(f"Template rendering took {(end_time - start_time) * 1000:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise
    return wrapper


class TemplateDebugger:
    """Template debugging utilities."""
    
    def __init__(self, template_engine: Jinja2TemplateEngine):
        self.template_engine = template_engine
        self.render_stats: Dict[str, Dict[str, Any]] = {}
    
    def debug_render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with debugging information."""
        start_time = time.time()
        
        try:
            result = self.template_engine.render(template_name, context)
            end_time = time.time()
            
            # Record statistics
            if template_name not in self.render_stats:
                self.render_stats[template_name] = {
                    "render_count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "last_render": None
                }
            
            stats = self.render_stats[template_name]
            stats["render_count"] += 1
            stats["total_time"] += (end_time - start_time)
            stats["avg_time"] = stats["total_time"] / stats["render_count"]
            stats["last_render"] = time.time()
            
            logger.debug(f"Template '{template_name}' rendered in {(end_time - start_time) * 1000:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Error rendering template '{template_name}': {e}")
            raise
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get template rendering statistics."""
        return self.render_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset template rendering statistics."""
        self.render_stats.clear()

    def debug_render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render template string with debugging information."""
        start_time = time.time()
        
        try:
            result = self.template_engine.render_string(template_string, context)
            end_time = time.time()
            
            # Record statistics
            if template_string not in self.render_stats:
                self.render_stats[template_string] = {
                    "render_count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "last_render": None
                }
            
            stats = self.render_stats[template_string]
            stats["render_count"] += 1
            stats["total_time"] += (end_time - start_time)
            stats["avg_time"] = stats["total_time"] / stats["render_count"]
            stats["last_render"] = time.time()
            
            logger.debug(f"Template string rendered in {(end_time - start_time) * 1000:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Error rendering template string: {e}")
            raise


def create_template_engine(
    template_dir: str = "templates",
    enable_cache: bool = True,
    enable_debug: bool = False,
    **kwargs
) -> Jinja2TemplateEngine:
    """
    Create template engine with specified configuration.
    
    Args:
        template_dir: Directory containing templates
        enable_cache: Enable template caching
        enable_debug: Enable template debugging
        **kwargs: Additional Jinja2 configuration options
    """
    if enable_cache:
        engine = CachedTemplateEngine(template_dir, enable_cache=True, **kwargs)
    else:
        engine = Jinja2TemplateEngine(template_dir, **kwargs)
    
    if enable_debug:
        debugger = TemplateDebugger(engine)
        # Replace render method with debug version
        engine.render = debugger.debug_render
        engine.debugger = debugger
    
    return engine 