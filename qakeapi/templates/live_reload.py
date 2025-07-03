"""
Live reload functionality for QakeAPI templates.
Provides automatic template reloading during development.
"""
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class TemplateChangeHandler(FileSystemEventHandler):
    """Handler for template file changes."""
    
    def __init__(self, callback: Callable[[str], None]):
        """
        Initialize template change handler.
        
        Args:
            callback: Function to call when template changes
        """
        self.callback = callback
        self.last_modified: Dict[str, float] = {}
        self.debounce_time = 0.5  # Debounce time in seconds
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        current_time = time.time()
        
        # Debounce rapid file changes
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < self.debounce_time:
                return
        
        self.last_modified[file_path] = current_time
        
        # Check if it's a template file
        if self._is_template_file(file_path):
            logger.info(f"Template file changed: {file_path}")
            self.callback(file_path)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if self._is_template_file(file_path):
            logger.info(f"Template file created: {file_path}")
            self.callback(file_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if self._is_template_file(file_path):
            logger.info(f"Template file deleted: {file_path}")
            self.callback(file_path)
    
    def _is_template_file(self, file_path: str) -> bool:
        """Check if file is a template file."""
        template_extensions = {'.html', '.htm', '.jinja', '.jinja2', '.j2', '.xml', '.txt'}
        return Path(file_path).suffix.lower() in template_extensions


class LiveReloadManager:
    """Manages live reload functionality for templates."""
    
    def __init__(self, template_dirs: List[str], enabled: bool = True):
        """
        Initialize live reload manager.
        
        Args:
            template_dirs: List of template directories to watch
            enabled: Whether live reload is enabled
        """
        self.template_dirs = [Path(d) for d in template_dirs]
        self.enabled = enabled
        self.observer: Optional[Observer] = None
        self.handlers: List[TemplateChangeHandler] = []
        self.callbacks: List[Callable[[str], None]] = []
        self.watched_files: Set[str] = set()
        
        if self.enabled:
            self._setup_watchers()
    
    def _setup_watchers(self):
        """Setup file system watchers."""
        if self.observer is None:
            self.observer = Observer()
        
        for template_dir in self.template_dirs:
            if template_dir.exists():
                handler = TemplateChangeHandler(self._on_template_change)
                self.handlers.append(handler)
                self.observer.schedule(handler, str(template_dir), recursive=True)
                logger.info(f"Watching template directory: {template_dir}")
    
    def start(self):
        """Start watching for template changes."""
        if not self.enabled or self.observer is None:
            return
        
        if not self.observer.is_alive():
            self.observer.start()
            logger.info("Live reload started")
    
    def stop(self):
        """Stop watching for template changes."""
        if self.observer is not None and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("Live reload stopped")
    
    def add_callback(self, callback: Callable[[str], None]):
        """Add callback function to be called when templates change."""
        self.callbacks.append(callback)
        logger.debug(f"Added live reload callback: {callback.__name__}")
    
    def remove_callback(self, callback: Callable[[str], None]):
        """Remove callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.debug(f"Removed live reload callback: {callback.__name__}")
    
    def _on_template_change(self, file_path: str):
        """Handle template change event."""
        logger.info(f"Template changed: {file_path}")
        for callback in self.callbacks:
            try:
                callback(file_path)
            except Exception as e:
                logger.error(f"Error in live reload callback: {e}")
    
    def get_watched_files(self) -> Set[str]:
        """Get set of currently watched files."""
        return self.watched_files.copy()
    
    def add_watch_file(self, file_path: str):
        """Add specific file to watch list."""
        self.watched_files.add(file_path)
    
    def remove_watch_file(self, file_path: str):
        """Remove specific file from watch list."""
        self.watched_files.discard(file_path)


class LiveReloadMiddleware:
    """Middleware for injecting live reload JavaScript into HTML responses."""
    
    def __init__(self, enabled: bool = True, port: int = 35729):
        """
        Initialize live reload middleware.
        
        Args:
            enabled: Whether live reload is enabled
            port: WebSocket port for live reload server
        """
        self.enabled = enabled
        self.port = port
        self.live_reload_script = self._generate_live_reload_script()
    
    def _generate_live_reload_script(self) -> str:
        """Generate live reload JavaScript code."""
        return f"""
<script>
(function() {{
    var script = document.createElement('script');
    script.src = 'http://localhost:{self.port}/livereload.js';
    document.head.appendChild(script);
}})();
</script>
"""
    
    async def __call__(self, request, handler):
        """Process request and inject live reload script if needed."""
        response = await handler(request)
        
        if not self.enabled:
            return response
        
        # Check if response is HTML
        content_type = response.headers.get(b'content-type', b'').decode('utf-8', 'ignore')
        if 'text/html' in content_type.lower():
            # Inject live reload script before closing body tag
            content = response.content.decode('utf-8', 'ignore')
            if '</body>' in content:
                content = content.replace('</body>', f'{self.live_reload_script}</body>')
            else:
                content += self.live_reload_script
            
            response.content = content.encode('utf-8')
        
        return response


# Global live reload manager instance
_live_reload_manager: Optional[LiveReloadManager] = None


def get_live_reload_manager() -> Optional[LiveReloadManager]:
    """Get global live reload manager instance."""
    return _live_reload_manager


def setup_live_reload(template_dirs: List[str], enabled: bool = True) -> LiveReloadManager:
    """
    Setup global live reload manager.
    
    Args:
        template_dirs: List of template directories to watch
        enabled: Whether live reload is enabled
    
    Returns:
        LiveReloadManager instance
    """
    global _live_reload_manager
    
    if _live_reload_manager is not None:
        _live_reload_manager.stop()
    
    _live_reload_manager = LiveReloadManager(template_dirs, enabled)
    return _live_reload_manager


def start_live_reload():
    """Start global live reload manager."""
    if _live_reload_manager is not None:
        _live_reload_manager.start()


def stop_live_reload():
    """Stop global live reload manager."""
    if _live_reload_manager is not None:
        _live_reload_manager.stop()


def add_live_reload_callback(callback: Callable[[str], None]):
    """Add callback to global live reload manager."""
    if _live_reload_manager is not None:
        _live_reload_manager.add_callback(callback)


def remove_live_reload_callback(callback: Callable[[str], None]):
    """Remove callback from global live reload manager."""
    if _live_reload_manager is not None:
        _live_reload_manager.remove_callback(callback) 