"""
Event-Driven Architecture System for QakeAPI

This module provides a comprehensive event system with:
- Event bus for loose coupling
- Event sourcing support
- Event replay and audit trails
- Saga pattern for distributed transactions
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from weakref import WeakSet

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for categorization"""
    DOMAIN = "domain"
    INTEGRATION = "integration"
    SYSTEM = "system"
    AUDIT = "audit"
    SAGA = "saga"


@dataclass
class Event:
    """Base event class"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.DOMAIN
    name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    source: str = ""
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=EventType(data.get("type", "domain")),
            name=data.get("name", ""),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            version=data.get("version", 1),
            source=data.get("source", ""),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id")
        )


class EventHandler(ABC):
    """Abstract base class for event handlers"""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event"""
        pass

    @property
    @abstractmethod
    def event_types(self) -> Set[EventType]:
        """Return set of event types this handler can process"""
        pass

    @property
    @abstractmethod
    def event_names(self) -> Set[str]:
        """Return set of event names this handler can process"""
        pass


class EventBus:
    """Event bus for loose coupling between components"""
    
    def __init__(self):
        self._handlers: Dict[str, Set[EventHandler]] = {}
        self._middleware: List[Callable] = []
        self._event_store: Optional["EventStore"] = None
        self._logger = logging.getLogger(f"{__name__}.EventBus")

    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler"""
        for event_type in handler.event_types:
            key = f"{event_type.value}:*"
            if key not in self._handlers:
                self._handlers[key] = set()
            self._handlers[key].add(handler)
        
        for event_name in handler.event_names:
            key = f"*:{event_name}"
            if key not in self._handlers:
                self._handlers[key] = set()
            self._handlers[key].add(handler)

    def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler"""
        for handlers in self._handlers.values():
            handlers.discard(handler)

    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the event bus"""
        self._middleware.append(middleware)

    def set_event_store(self, event_store: "EventStore") -> None:
        """Set event store for persistence"""
        self._event_store = event_store

    async def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers"""
        self._logger.debug(f"Publishing event: {event.name} ({event.id})")
        
        # Apply middleware
        for middleware in self._middleware:
            event = await middleware(event)
        
        # Store event if event store is configured
        if self._event_store:
            await self._event_store.store(event)
        
        # Find matching handlers
        handlers = set()
        
        # Add handlers for specific event type and name
        specific_key = f"{event.type.value}:{event.name}"
        if specific_key in self._handlers:
            handlers.update(self._handlers[specific_key])
        
        # Add handlers for event type only
        type_key = f"{event.type.value}:*"
        if type_key in self._handlers:
            handlers.update(self._handlers[type_key])
        
        # Add handlers for event name only
        name_key = f"*:{event.name}"
        if name_key in self._handlers:
            handlers.update(self._handlers[name_key])
        
        # Execute handlers
        tasks = []
        for handler in handlers:
            try:
                task = asyncio.create_task(handler.handle(event))
                tasks.append(task)
            except Exception as e:
                self._logger.error(f"Error creating task for handler {handler}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class EventStore:
    """Event store for event sourcing"""
    
    def __init__(self, storage_backend: Optional["EventStorageBackend"] = None):
        self._storage = storage_backend or InMemoryEventStorage()
        self._logger = logging.getLogger(f"{__name__}.EventStore")

    async def store(self, event: Event) -> None:
        """Store an event"""
        await self._storage.store(event)
        self._logger.debug(f"Stored event: {event.id}")

    async def get_events(self, 
                        aggregate_id: Optional[str] = None,
                        event_type: Optional[EventType] = None,
                        event_name: Optional[str] = None,
                        from_timestamp: Optional[datetime] = None,
                        to_timestamp: Optional[datetime] = None,
                        limit: Optional[int] = None) -> List[Event]:
        """Retrieve events with filters"""
        return await self._storage.get_events(
            aggregate_id=aggregate_id,
            event_type=event_type,
            event_name=event_name,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit
        )

    async def replay_events(self, 
                           handler: EventHandler,
                           aggregate_id: Optional[str] = None,
                           from_timestamp: Optional[datetime] = None) -> None:
        """Replay events for a handler"""
        events = await self.get_events(
            aggregate_id=aggregate_id,
            from_timestamp=from_timestamp
        )
        
        for event in events:
            if (event.type in handler.event_types or 
                event.name in handler.event_names):
                await handler.handle(event)


class EventStorageBackend(ABC):
    """Abstract base class for event storage backends"""
    
    @abstractmethod
    async def store(self, event: Event) -> None:
        """Store an event"""
        pass
    
    @abstractmethod
    async def get_events(self, 
                        aggregate_id: Optional[str] = None,
                        event_type: Optional[EventType] = None,
                        event_name: Optional[str] = None,
                        from_timestamp: Optional[datetime] = None,
                        to_timestamp: Optional[datetime] = None,
                        limit: Optional[int] = None) -> List[Event]:
        """Retrieve events with filters"""
        pass


class InMemoryEventStorage(EventStorageBackend):
    """In-memory event storage for testing and development"""
    
    def __init__(self):
        self._events: List[Event] = []
        self._logger = logging.getLogger(f"{__name__}.InMemoryEventStorage")

    async def store(self, event: Event) -> None:
        """Store an event in memory"""
        self._events.append(event)
        self._logger.debug(f"Stored event in memory: {event.id}")

    async def get_events(self, 
                        aggregate_id: Optional[str] = None,
                        event_type: Optional[EventType] = None,
                        event_name: Optional[str] = None,
                        from_timestamp: Optional[datetime] = None,
                        to_timestamp: Optional[datetime] = None,
                        limit: Optional[int] = None) -> List[Event]:
        """Retrieve events with filters"""
        events = self._events.copy()
        
        # Apply filters
        if aggregate_id:
            events = [e for e in events if e.metadata.get("aggregate_id") == aggregate_id]
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        
        if to_timestamp:
            events = [e for e in events if e.timestamp <= to_timestamp]
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        # Apply limit
        if limit:
            events = events[:limit]
        
        return events


class SagaStep:
    """Single step in a saga"""
    
    def __init__(self, 
                 name: str,
                 action: Callable,
                 compensation: Optional[Callable] = None):
        self.name = name
        self.action = action
        self.compensation = compensation
        self.completed = False
        self.compensated = False


class Saga:
    """Saga pattern implementation for distributed transactions"""
    
    def __init__(self, name: str, correlation_id: str):
        self.name = name
        self.correlation_id = correlation_id
        self.steps: List[SagaStep] = []
        self.current_step = 0
        self.completed = False
        self.failed = False
        self.logger = logging.getLogger(f"{__name__}.Saga")

    def add_step(self, name: str, action: Callable, compensation: Optional[Callable] = None) -> None:
        """Add a step to the saga"""
        step = SagaStep(name, action, compensation)
        self.steps.append(step)

    async def execute(self) -> bool:
        """Execute the saga"""
        self.logger.info(f"Starting saga: {self.name} ({self.correlation_id})")
        
        try:
            for i, step in enumerate(self.steps):
                self.current_step = i
                self.logger.info(f"Executing step: {step.name}")
                
                try:
                    if asyncio.iscoroutinefunction(step.action):
                        await step.action()
                    else:
                        step.action()
                    
                    step.completed = True
                    self.logger.info(f"Step completed: {step.name}")
                    
                except Exception as e:
                    self.logger.error(f"Step failed: {step.name} - {e}")
                    await self._compensate()
                    self.failed = True
                    return False
            
            self.completed = True
            self.logger.info(f"Saga completed successfully: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Saga failed: {self.name} - {e}")
            await self._compensate()
            self.failed = True
            return False

    async def _compensate(self) -> None:
        """Compensate for completed steps"""
        self.logger.info(f"Starting compensation for saga: {self.name}")
        
        for i in range(self.current_step - 1, -1, -1):
            step = self.steps[i]
            if step.completed and step.compensation:
                try:
                    self.logger.info(f"Compensating step: {step.name}")
                    
                    if asyncio.iscoroutinefunction(step.compensation):
                        await step.compensation()
                    else:
                        step.compensation()
                    
                    step.compensated = True
                    self.logger.info(f"Step compensated: {step.name}")
                    
                except Exception as e:
                    self.logger.error(f"Compensation failed: {step.name} - {e}")


class SagaManager:
    """Manager for saga execution and monitoring"""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self.active_sagas: Dict[str, Saga] = {}
        self.completed_sagas: List[Saga] = []
        self.logger = logging.getLogger(f"{__name__}.SagaManager")

    async def start_saga(self, saga: Saga) -> bool:
        """Start a saga execution"""
        self.active_sagas[saga.correlation_id] = saga
        
        # Publish saga started event
        if self.event_bus:
            event = Event(
                type=EventType.SAGA,
                name="saga.started",
                data={"saga_name": saga.name, "correlation_id": saga.correlation_id},
                correlation_id=saga.correlation_id
            )
            await self.event_bus.publish(event)
        
        # Execute saga
        success = await saga.execute()
        
        # Move to completed list
        del self.active_sagas[saga.correlation_id]
        self.completed_sagas.append(saga)
        
        # Publish saga completed/failed event
        if self.event_bus:
            event_name = "saga.completed" if success else "saga.failed"
            event = Event(
                type=EventType.SAGA,
                name=event_name,
                data={"saga_name": saga.name, "correlation_id": saga.correlation_id},
                correlation_id=saga.correlation_id
            )
            await self.event_bus.publish(event)
        
        return success

    def get_saga_status(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a saga"""
        # Check active sagas
        if correlation_id in self.active_sagas:
            saga = self.active_sagas[correlation_id]
            return {
                "name": saga.name,
                "correlation_id": saga.correlation_id,
                "status": "active",
                "current_step": saga.current_step,
                "total_steps": len(saga.steps)
            }
        
        # Check completed sagas
        for saga in self.completed_sagas:
            if saga.correlation_id == correlation_id:
                return {
                    "name": saga.name,
                    "correlation_id": saga.correlation_id,
                    "status": "completed" if saga.completed else "failed",
                    "total_steps": len(saga.steps)
                }
        
        return None


# Global event bus instance
event_bus = EventBus() 