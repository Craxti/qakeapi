"""
Tests for Event-Driven Architecture System

Tests cover:
- Event bus functionality
- Event handlers
- Event store operations
- Saga pattern
- Event replay
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from qakeapi.core.events import (
    Event, EventType, EventBus, EventStore, InMemoryEventStorage,
    EventHandler, Saga, SagaManager
)


class TestEventHandler(EventHandler):
    """Test event handler for testing"""
    
    def __init__(self):
        self.handled_events = []
        self.event_types_set = {EventType.DOMAIN}
        self.event_names_set = {"test.event"}
    
    @property
    def event_types(self):
        return self.event_types_set
    
    @property
    def event_names(self):
        return self.event_names_set
    
    async def handle(self, event: Event) -> None:
        self.handled_events.append(event)


class TestEvent:
    """Test Event class"""
    
    def test_event_creation(self):
        """Test event creation with default values"""
        event = Event()
        assert event.id is not None
        assert event.type == EventType.DOMAIN
        assert event.name == ""
        assert event.data == {}
        assert event.metadata == {}
        assert isinstance(event.timestamp, datetime)
        assert event.version == 1
        assert event.source == ""
        assert event.correlation_id is None
        assert event.causation_id is None
    
    def test_event_creation_with_values(self):
        """Test event creation with specific values"""
        event = Event(
            id="test-id",
            type=EventType.SYSTEM,
            name="test.event",
            data={"key": "value"},
            metadata={"meta": "data"},
            version=2,
            source="test-source",
            correlation_id="corr-id",
            causation_id="cause-id"
        )
        
        assert event.id == "test-id"
        assert event.type == EventType.SYSTEM
        assert event.name == "test.event"
        assert event.data == {"key": "value"}
        assert event.metadata == {"meta": "data"}
        assert event.version == 2
        assert event.source == "test-source"
        assert event.correlation_id == "corr-id"
        assert event.causation_id == "cause-id"
    
    def test_event_to_dict(self):
        """Test event serialization to dictionary"""
        event = Event(
            id="test-id",
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value"},
            correlation_id="corr-id"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["id"] == "test-id"
        assert event_dict["type"] == "domain"
        assert event_dict["name"] == "test.event"
        assert event_dict["data"] == {"key": "value"}
        assert event_dict["correlation_id"] == "corr-id"
        assert "timestamp" in event_dict
    
    def test_event_from_dict(self):
        """Test event deserialization from dictionary"""
        event_dict = {
            "id": "test-id",
            "type": "system",
            "name": "test.event",
            "data": {"key": "value"},
            "metadata": {"meta": "data"},
            "timestamp": "2023-01-01T12:00:00",
            "version": 2,
            "source": "test-source",
            "correlation_id": "corr-id"
        }
        
        event = Event.from_dict(event_dict)
        
        assert event.id == "test-id"
        assert event.type == EventType.SYSTEM
        assert event.name == "test.event"
        assert event.data == {"key": "value"}
        assert event.metadata == {"meta": "data"}
        assert event.version == 2
        assert event.source == "test-source"
        assert event.correlation_id == "corr-id"


class TestEventBus:
    """Test EventBus class"""
    
    @pytest.fixture
    def event_bus(self):
        return EventBus()
    
    @pytest.fixture
    def handler(self):
        return TestEventHandler()
    
    def test_event_bus_initialization(self, event_bus):
        """Test event bus initialization"""
        assert event_bus._handlers == {}
        assert event_bus._middleware == []
        assert event_bus._event_store is None
    
    def test_register_handler(self, event_bus, handler):
        """Test handler registration"""
        event_bus.register_handler(handler)
        
        # Check that handlers are registered for event types
        assert "domain:*" in event_bus._handlers
        assert handler in event_bus._handlers["domain:*"]
        
        # Check that handlers are registered for event names
        assert "*:test.event" in event_bus._handlers
        assert handler in event_bus._handlers["*:test.event"]
    
    def test_unregister_handler(self, event_bus, handler):
        """Test handler unregistration"""
        event_bus.register_handler(handler)
        event_bus.unregister_handler(handler)
        
        # Check that handlers are removed
        assert handler not in event_bus._handlers["domain:*"]
        assert handler not in event_bus._handlers["*:test.event"]
    
    def test_add_middleware(self, event_bus):
        """Test middleware addition"""
        middleware = Mock()
        event_bus.add_middleware(middleware)
        
        assert middleware in event_bus._middleware
    
    def test_set_event_store(self, event_bus):
        """Test event store setting"""
        event_store = Mock()
        event_bus.set_event_store(event_store)
        
        assert event_bus._event_store == event_store
    
    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus, handler):
        """Test event publishing"""
        event_bus.register_handler(handler)
        
        event = Event(
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value"}
        )
        
        await event_bus.publish(event)
        
        # Check that handler received the event
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0] == event
    
    @pytest.mark.asyncio
    async def test_publish_event_with_middleware(self, event_bus, handler):
        """Test event publishing with middleware"""
        event_bus.register_handler(handler)
        
        # Add middleware that modifies the event
        async def middleware(event):
            event.data["modified"] = True
            return event
        
        event_bus.add_middleware(middleware)
        
        event = Event(
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value"}
        )
        
        await event_bus.publish(event)
        
        # Check that middleware was applied
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].data["modified"] is True
    
    @pytest.mark.asyncio
    async def test_publish_event_with_event_store(self, event_bus, handler):
        """Test event publishing with event store"""
        event_store = Mock()
        event_store.store = AsyncMock()
        event_bus.set_event_store(event_store)
        event_bus.register_handler(handler)
        
        event = Event(
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value"}
        )
        
        await event_bus.publish(event)
        
        # Check that event was stored
        event_store.store.assert_called_once_with(event)
        
        # Check that handler received the event
        assert len(handler.handled_events) == 1


class TestEventStore:
    """Test EventStore class"""
    
    @pytest.fixture
    def event_store(self):
        storage = InMemoryEventStorage()
        return EventStore(storage)
    
    @pytest.mark.asyncio
    async def test_store_event(self, event_store):
        """Test event storage"""
        event = Event(
            id="test-id",
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value"}
        )
        
        await event_store.store(event)
        
        # Retrieve events
        events = await event_store.get_events()
        assert len(events) == 1
        assert events[0].id == "test-id"
    
    @pytest.mark.asyncio
    async def test_get_events_with_filters(self, event_store):
        """Test event retrieval with filters"""
        # Create test events
        event1 = Event(
            id="event1",
            type=EventType.DOMAIN,
            name="order.created",
            data={"order_id": "order1"},
            metadata={"aggregate_id": "order1"}
        )
        
        event2 = Event(
            id="event2",
            type=EventType.SYSTEM,
            name="system.startup",
            data={"service": "test"}
        )
        
        event3 = Event(
            id="event3",
            type=EventType.DOMAIN,
            name="order.confirmed",
            data={"order_id": "order1"},
            metadata={"aggregate_id": "order1"}
        )
        
        # Store events
        await event_store.store(event1)
        await event_store.store(event2)
        await event_store.store(event3)
        
        # Test filtering by aggregate_id
        events = await event_store.get_events(aggregate_id="order1")
        assert len(events) == 2
        assert all(e.metadata.get("aggregate_id") == "order1" for e in events)
        
        # Test filtering by event_type
        events = await event_store.get_events(event_type=EventType.DOMAIN)
        assert len(events) == 2
        assert all(e.type == EventType.DOMAIN for e in events)
        
        # Test filtering by event_name
        events = await event_store.get_events(event_name="order.created")
        assert len(events) == 1
        assert events[0].name == "order.created"
        
        # Test filtering by timestamp
        from_timestamp = datetime.utcnow() + timedelta(seconds=1)
        events = await event_store.get_events(from_timestamp=from_timestamp)
        assert len(events) == 0
        
        # Test limit
        events = await event_store.get_events(limit=2)
        assert len(events) == 2
    
    @pytest.mark.asyncio
    async def test_replay_events(self, event_store):
        """Test event replay"""
        handler = TestEventHandler()
        
        # Create and store events
        event1 = Event(
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value1"}
        )
        
        event2 = Event(
            type=EventType.DOMAIN,
            name="test.event",
            data={"key": "value2"}
        )
        
        await event_store.store(event1)
        await event_store.store(event2)
        
        # Replay events
        await event_store.replay_events(handler)
        
        # Check that handler received events
        assert len(handler.handled_events) == 2
        assert handler.handled_events[0].data["key"] == "value1"
        assert handler.handled_events[1].data["key"] == "value2"


class TestSaga:
    """Test Saga class"""
    
    def test_saga_initialization(self):
        """Test saga initialization"""
        saga = Saga("test_saga", "corr-id")
        
        assert saga.name == "test_saga"
        assert saga.correlation_id == "corr-id"
        assert saga.steps == []
        assert saga.current_step == 0
        assert not saga.completed
        assert not saga.failed
    
    def test_add_step(self):
        """Test adding steps to saga"""
        saga = Saga("test_saga", "corr-id")
        
        action = Mock()
        compensation = Mock()
        
        saga.add_step("step1", action, compensation)
        
        assert len(saga.steps) == 1
        assert saga.steps[0].name == "step1"
        assert saga.steps[0].action == action
        assert saga.steps[0].compensation == compensation
        assert not saga.steps[0].completed
        assert not saga.steps[0].compensated
    
    @pytest.mark.asyncio
    async def test_saga_execution_success(self):
        """Test successful saga execution"""
        saga = Saga("test_saga", "corr-id")
        
        # Mock actions
        action1 = AsyncMock()
        action2 = AsyncMock()
        
        saga.add_step("step1", action1)
        saga.add_step("step2", action2)
        
        # Execute saga
        result = await saga.execute()
        
        assert result is True
        assert saga.completed
        assert not saga.failed
        assert action1.called
        assert action2.called
        assert saga.steps[0].completed
        assert saga.steps[1].completed
    
    @pytest.mark.asyncio
    async def test_saga_execution_failure_with_compensation(self):
        """Test saga execution failure with compensation"""
        saga = Saga("test_saga", "corr-id")
        
        # Mock actions and compensations
        action1 = AsyncMock()
        action2 = AsyncMock(side_effect=Exception("Step 2 failed"))
        compensation1 = AsyncMock()
        
        saga.add_step("step1", action1, compensation1)
        saga.add_step("step2", action2)
        
        # Execute saga
        result = await saga.execute()
        
        assert result is False
        assert not saga.completed
        assert saga.failed
        assert action1.called
        assert action2.called
        assert compensation1.called  # Compensation should be called
        assert saga.steps[0].compensated


class TestSagaManager:
    """Test SagaManager class"""
    
    @pytest.fixture
    def event_bus(self):
        return EventBus()
    
    @pytest.fixture
    def saga_manager(self, event_bus):
        return SagaManager(event_bus)
    
    def test_saga_manager_initialization(self, saga_manager):
        """Test saga manager initialization"""
        assert saga_manager.event_bus is not None
        assert saga_manager.active_sagas == {}
        assert saga_manager.completed_sagas == []
    
    @pytest.mark.asyncio
    async def test_start_saga_success(self, saga_manager):
        """Test successful saga start"""
        saga = Saga("test_saga", "corr-id")
        
        # Add a simple step
        action = AsyncMock()
        saga.add_step("step1", action)
        
        # Start saga
        result = await saga_manager.start_saga(saga)
        
        assert result is True
        assert "corr-id" not in saga_manager.active_sagas
        assert len(saga_manager.completed_sagas) == 1
        assert saga_manager.completed_sagas[0] == saga
    
    @pytest.mark.asyncio
    async def test_start_saga_failure(self, saga_manager):
        """Test failed saga start"""
        saga = Saga("test_saga", "corr-id")
        
        # Add a step that fails
        action = AsyncMock(side_effect=Exception("Saga failed"))
        saga.add_step("step1", action)
        
        # Start saga
        result = await saga_manager.start_saga(saga)
        
        assert result is False
        assert "corr-id" not in saga_manager.active_sagas
        assert len(saga_manager.completed_sagas) == 1
        assert saga_manager.completed_sagas[0] == saga
    
    def test_get_saga_status_active(self, saga_manager):
        """Test getting status of active saga"""
        saga = Saga("test_saga", "corr-id")
        saga_manager.active_sagas["corr-id"] = saga
        
        status = saga_manager.get_saga_status("corr-id")
        
        assert status is not None
        assert status["name"] == "test_saga"
        assert status["correlation_id"] == "corr-id"
        assert status["status"] == "active"
    
    def test_get_saga_status_completed(self, saga_manager):
        """Test getting status of completed saga"""
        saga = Saga("test_saga", "corr-id")
        saga.completed = True
        saga_manager.completed_sagas.append(saga)
        
        status = saga_manager.get_saga_status("corr-id")
        
        assert status is not None
        assert status["name"] == "test_saga"
        assert status["correlation_id"] == "corr-id"
        assert status["status"] == "completed"
    
    def test_get_saga_status_not_found(self, saga_manager):
        """Test getting status of non-existent saga"""
        status = saga_manager.get_saga_status("non-existent")
        
        assert status is None


class TestInMemoryEventStorage:
    """Test InMemoryEventStorage class"""
    
    @pytest.fixture
    def storage(self):
        return InMemoryEventStorage()
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_events(self, storage):
        """Test storing and retrieving events"""
        event1 = Event(id="event1", name="test1")
        event2 = Event(id="event2", name="test2")
        
        await storage.store(event1)
        await storage.store(event2)
        
        events = await storage.get_events()
        assert len(events) == 2
        assert events[0].id == "event1"
        assert events[1].id == "event2"
    
    @pytest.mark.asyncio
    async def test_get_events_with_filters(self, storage):
        """Test retrieving events with various filters"""
        event1 = Event(
            id="event1",
            type=EventType.DOMAIN,
            name="order.created",
            metadata={"aggregate_id": "order1"}
        )
        
        event2 = Event(
            id="event2",
            type=EventType.SYSTEM,
            name="system.startup"
        )
        
        await storage.store(event1)
        await storage.store(event2)
        
        # Test aggregate_id filter
        events = await storage.get_events(aggregate_id="order1")
        assert len(events) == 1
        assert events[0].id == "event1"
        
        # Test event_type filter
        events = await storage.get_events(event_type=EventType.DOMAIN)
        assert len(events) == 1
        assert events[0].id == "event1"
        
        # Test event_name filter
        events = await storage.get_events(event_name="system.startup")
        assert len(events) == 1
        assert events[0].id == "event2"
        
        # Test limit
        events = await storage.get_events(limit=1)
        assert len(events) == 1


if __name__ == "__main__":
    pytest.main([__file__]) 