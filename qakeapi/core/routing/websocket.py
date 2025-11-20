"""WebSocket routing implementation."""
import re
import logging
import asyncio
from typing import Any, Callable, Dict, Optional, Pattern, Tuple

from ..websockets import WebSocketConnection as WebSocket
from .base import BaseRoute, BaseRouter

logger = logging.getLogger(__name__)

class WebSocketRoute(BaseRoute):
    """WebSocket route implementation."""
    
    def __init__(self, path: str, handler: Callable, name: Optional[str] = None):
        super().__init__(path, handler, name)
        logger.debug(f"Created WebSocket route: {path}")
    
    def _compile_pattern(self, path: str) -> Pattern:
        """Compile path pattern to regex."""
        pattern = path.replace("/", "\\/")
        pattern = pattern.replace("{", "(?P<").replace("}", ">[^/]+)")
        return re.compile(f"^{pattern}$")
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Check if path matches route pattern."""
        match = self.pattern.match(path)
        if match:
            logger.debug(f"WebSocket route {self.path} matches {path}")
            return match.groupdict()
        logger.debug(f"WebSocket route {self.path} does not match {path}")
        return None

class WebSocketRouter(BaseRouter):
    """WebSocket router implementation."""
    
    def add_route(self, path: str, handler: Callable, name: Optional[str] = None) -> None:
        """Add WebSocket route."""
        # Check for existing route
        for existing_route in self.routes:
            if existing_route.path == path:
                logger.debug(f"Updating existing WebSocket route: {path}")
                if isinstance(existing_route, WebSocketRoute):
                    existing_route.handler = handler
                    existing_route.name = name
                    return
        
        route = WebSocketRoute(path, handler, name)
        self.routes.append(route)
        logger.debug(f"Added WebSocket route: {path}")
    
    def websocket(self, path: str, name: Optional[str] = None):
        """WebSocket route decorator."""
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, name)
            return handler
        return decorator
    
    async def handle_request(self, websocket: WebSocket) -> None:
        """Handle WebSocket connection."""
        try:
            path = websocket.path
            logger.debug(f"Handling WebSocket connection: {path}")
            
            # Find matching route
            for route in self.routes:
                if not isinstance(route, WebSocketRoute):
                    continue
                    
                params = route.match(path)
                if params is not None:
                    # Add path parameters
                    websocket.path_params.update(params)
                    
                    # Apply middleware chain
                    handler = route.handler
                    for middleware in reversed(self._middleware):
                        if asyncio.iscoroutinefunction(middleware):
                            prev_handler = handler
                            async def wrapped_handler(ws, prev_handler=prev_handler):
                                return await middleware(ws, prev_handler)
                            handler = wrapped_handler
                        else:
                            handler = middleware(handler)
                    
                    # Handle connection
                    logger.debug(f"Calling WebSocket handler for {path}")
                    await handler(websocket)
                    return
            
            logger.debug(f"No WebSocket route found for {path}")
            await websocket.close(1000, "No route found")
            
        except Exception as e:
            logger.error(f"Error handling WebSocket: {str(e)}", exc_info=True)
            try:
                await websocket.close(1011, "Internal server error")
            except:
                pass

    def find_route(self, path: str, route_type: str = "websocket") -> Optional[Tuple[WebSocketRoute, Dict[str, str]]]:
        """Find route by path and type"""
        logger.debug(f"Finding WebSocket route for path: {path} type: {route_type}")
        
        for route in self.routes:
            if not isinstance(route, WebSocketRoute):
                continue
                
            params = route.match(path)
            if params is not None:
                logger.debug(f"Found WebSocket route: {route.path}")
                return route, params
        
        logger.debug(f"No WebSocket route found for path: {path}")
        return None 