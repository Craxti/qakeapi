"""
Reactive Engine - Event-driven reactive system.

This module provides reactive event handling capabilities,
allowing functions to react to events in the application.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


@dataclass
class Event:
    """Represents an event in the system."""
    
    name: str
    data: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    
    def __post_init__(self):
        """Initialize event."""
        if not isinstance(self.name, str):
            raise ValueError("Event name must be a string")


class EventBus:
    """
    Event bus for reactive event handling.
    
    Allows functions to subscribe to events and react to them.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._handlers: Dict[str, List[Callable[..., Any]]] = {}
        self._global_handlers: List[Callable[..., Any]] = []
    
    def subscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """
        Subscribe handler to event.
        
        Args:
            event_name: Event name to subscribe to
            handler: Handler function
            
        Example:
            ```python
            def on_user_created(user):
                print(f"User created: {user}")
            
            event_bus.subscribe("user:created", on_user_created)
            ```
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def subscribe_all(self, handler: Callable[..., Any]) -> None:
        """
        Subscribe handler to all events.
        
        Args:
            handler: Handler function that will receive all events
        """
        self._global_handlers.append(handler)
    
    async def emit(self, event_name: str, data: Any = None) -> None:
        """
        Emit event.
        
        Args:
            event_name: Event name
            data: Event data
            
        Example:
            ```python
            await event_bus.emit("user:created", {"id": 1, "name": "John"})
            ```
        """
        event = Event(name=event_name, data=data)
        
        # Collect handlers
        handlers = []
        
        # Specific handlers
        if event_name in self._handlers:
            handlers.extend(self._handlers[event_name])
        
        # Global handlers
        handlers.extend(self._global_handlers)
        
        # Execute handlers
        if handlers:
            tasks = []
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    # Sync handler - run in executor
                    loop = asyncio.get_event_loop()
                    tasks.append(
                        loop.run_in_executor(None, lambda: handler(event))
                    )
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def unsubscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """
        Unsubscribe handler from event.
        
        Args:
            event_name: Event name
            handler: Handler function to remove
        """
        if event_name in self._handlers:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)


# Global event bus instance
_event_bus = EventBus()


def react(event_name: str):
    """
    Reactive decorator - register function to react to events.
    
    Args:
        event_name: Event name to react to
        
    Example:
        ```python
        @react("user:created")
        async def on_user_created(event):
            print(f"User created: {event.data}")
        ```
    """
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        _event_bus.subscribe(event_name, handler)
        return handler
    
    return decorator


async def emit(event_name: str, data: Any = None) -> None:
    """
    Emit event to event bus.
    
    Args:
        event_name: Event name
        data: Event data
        
    Example:
        ```python
        await emit("user:created", {"id": 1, "name": "John"})
        ```
    """
    await _event_bus.emit(event_name, data)


