"""
Tests for Reactive Events system.
"""

import pytest
import asyncio
from qakeapi.core.reactive import Event, EventBus, emit, react


class TestEvent:
    """Tests for Event class."""
    
    def test_event_creation(self):
        """Test event creation."""
        event = Event("user:created", {"id": 1, "name": "John"})
        
        assert event.name == "user:created"
        assert event.data == {"id": 1, "name": "John"}


class TestEventBus:
    """Tests for EventBus."""
    
    def test_event_bus_creation(self):
        """Test EventBus creation."""
        bus = EventBus()
        assert bus._handlers == {}
    
    @pytest.mark.asyncio
    async def test_subscribe_and_emit(self):
        """Test subscribing to events and emitting."""
        bus = EventBus()
        results = []
        
        async def handler(event: Event):
            results.append(event.data)
        
        bus.subscribe("user:created", handler)
        await bus.emit("user:created", {"id": 1, "name": "John"})
        
        # Give handlers time to execute
        await asyncio.sleep(0.01)
        
        assert len(results) == 1
        assert results[0] == {"id": 1, "name": "John"}
    
    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        """Test multiple handlers for same event."""
        bus = EventBus()
        results = []
        
        async def handler1(event: Event):
            results.append(f"handler1: {event.data}")
        
        async def handler2(event: Event):
            results.append(f"handler2: {event.data}")
        
        bus.subscribe("user:created", handler1)
        bus.subscribe("user:created", handler2)
        
        await bus.emit("user:created", {"id": 1})
        
        # Give handlers time to execute
        await asyncio.sleep(0.01)
        
        assert len(results) == 2
        assert "handler1" in results[0]
        assert "handler2" in results[1]
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        results = []
        
        async def handler(event: Event):
            results.append(event.data)
        
        bus.subscribe("user:created", handler)
        bus.unsubscribe("user:created", handler)
        
        await bus.emit("user:created", {"id": 1})
        
        # Give handlers time to execute
        await asyncio.sleep(0.01)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_emit_no_handlers(self):
        """Test emitting event with no handlers."""
        bus = EventBus()
        
        # Should not raise an error
        await bus.emit("unknown:event", {"data": "test"})


class TestEmit:
    """Tests for global emit function."""
    
    @pytest.mark.asyncio
    async def test_global_emit(self):
        """Test global emit function."""
        results = []
        
        async def handler(event: Event):
            results.append(event.data)
        
        # Get global event bus
        from qakeapi.core.reactive import _event_bus
        _event_bus.subscribe("test:event", handler)
        
        await emit("test:event", {"message": "test"})
        
        # Give handlers time to execute
        await asyncio.sleep(0.01)
        
        assert len(results) == 1
        assert results[0] == {"message": "test"}


class TestReact:
    """Tests for react decorator."""
    
    @pytest.mark.asyncio
    async def test_react_decorator(self):
        """Test react decorator."""
        results = []
        
        @react("test:event")
        async def handler(event: Event):
            results.append(event.data)
        
        from qakeapi.core.reactive import _event_bus
        await _event_bus.emit("test:event", {"message": "test"})
        
        # Give handlers time to execute
        await asyncio.sleep(0.01)
        
        assert len(results) == 1

