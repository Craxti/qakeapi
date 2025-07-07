"""
Event-Driven Architecture Example Application

This example demonstrates:
- Event bus for loose coupling
- Event sourcing with event store
- Saga pattern for distributed transactions
- Event handlers and middleware
- Event replay and audit trails
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append('..')

from qakeapi import QakeAPI
from qakeapi.core.events import (
    Event, EventType, EventBus, EventStore, InMemoryEventStorage,
    EventHandler, Saga, SagaManager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create application
app = QakeAPI("Event-Driven Architecture Example")

# Initialize event system
event_bus = EventBus()
event_store = EventStore(InMemoryEventStorage())
saga_manager = SagaManager(event_bus)

# Connect event bus to event store
event_bus.set_event_store(event_store)


class OrderEventHandler(EventHandler):
    """Handler for order-related events"""
    
    def __init__(self):
        self.orders: Dict[str, Dict[str, Any]] = {}
    
    @property
    def event_types(self):
        return {EventType.DOMAIN}
    
    @property
    def event_names(self):
        return {"order.created", "order.confirmed", "order.cancelled"}
    
    async def handle(self, event: Event) -> None:
        logger.info(f"OrderEventHandler processing: {event.name}")
        
        if event.name == "order.created":
            order_id = event.data.get("order_id")
            self.orders[order_id] = {
                "id": order_id,
                "status": "created",
                "items": event.data.get("items", []),
                "total": event.data.get("total", 0),
                "created_at": event.timestamp
            }
            logger.info(f"Order created: {order_id}")
            
        elif event.name == "order.confirmed":
            order_id = event.data.get("order_id")
            if order_id in self.orders:
                self.orders[order_id]["status"] = "confirmed"
                self.orders[order_id]["confirmed_at"] = event.timestamp
                logger.info(f"Order confirmed: {order_id}")
                
        elif event.name == "order.cancelled":
            order_id = event.data.get("order_id")
            if order_id in self.orders:
                self.orders[order_id]["status"] = "cancelled"
                self.orders[order_id]["cancelled_at"] = event.timestamp
                logger.info(f"Order cancelled: {order_id}")


class PaymentEventHandler(EventHandler):
    """Handler for payment-related events"""
    
    def __init__(self):
        self.payments: Dict[str, Dict[str, Any]] = {}
    
    @property
    def event_types(self):
        return {EventType.DOMAIN}
    
    @property
    def event_names(self):
        return {"payment.processed", "payment.failed", "payment.refunded"}
    
    async def handle(self, event: Event) -> None:
        logger.info(f"PaymentEventHandler processing: {event.name}")
        
        if event.name == "payment.processed":
            payment_id = event.data.get("payment_id")
            self.payments[payment_id] = {
                "id": payment_id,
                "order_id": event.data.get("order_id"),
                "amount": event.data.get("amount", 0),
                "status": "processed",
                "processed_at": event.timestamp
            }
            logger.info(f"Payment processed: {payment_id}")
            
        elif event.name == "payment.failed":
            payment_id = event.data.get("payment_id")
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "failed"
                self.payments[payment_id]["failed_at"] = event.timestamp
                logger.info(f"Payment failed: {payment_id}")
                
        elif event.name == "payment.refunded":
            payment_id = event.data.get("payment_id")
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "refunded"
                self.payments[payment_id]["refunded_at"] = event.timestamp
                logger.info(f"Payment refunded: {payment_id}")


class InventoryEventHandler(EventHandler):
    """Handler for inventory-related events"""
    
    def __init__(self):
        self.inventory: Dict[str, int] = {"item1": 100, "item2": 50, "item3": 75}
    
    @property
    def event_types(self):
        return {EventType.DOMAIN}
    
    @property
    def event_names(self):
        return {"inventory.reserved", "inventory.released", "inventory.updated"}
    
    async def handle(self, event: Event) -> None:
        logger.info(f"InventoryEventHandler processing: {event.name}")
        
        if event.name == "inventory.reserved":
            item_id = event.data.get("item_id")
            quantity = event.data.get("quantity", 0)
            if item_id in self.inventory:
                self.inventory[item_id] -= quantity
                logger.info(f"Inventory reserved: {item_id} (-{quantity})")
                
        elif event.name == "inventory.released":
            item_id = event.data.get("item_id")
            quantity = event.data.get("quantity", 0)
            if item_id in self.inventory:
                self.inventory[item_id] += quantity
                logger.info(f"Inventory released: {item_id} (+{quantity})")
                
        elif event.name == "inventory.updated":
            item_id = event.data.get("item_id")
            quantity = event.data.get("quantity", 0)
            self.inventory[item_id] = quantity
            logger.info(f"Inventory updated: {item_id} = {quantity}")


class AuditEventHandler(EventHandler):
    """Handler for audit events"""
    
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
    
    @property
    def event_types(self):
        return {EventType.AUDIT, EventType.SAGA}
    
    @property
    def event_names(self):
        return set()  # Handle by event type only
    
    async def handle(self, event: Event) -> None:
        audit_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.id,
            "event_name": event.name,
            "event_type": event.type.value,
            "correlation_id": event.correlation_id,
            "data": event.data
        }
        self.audit_log.append(audit_entry)
        logger.info(f"Audit log entry: {event.name} ({event.id})")


# Register event handlers
order_handler = OrderEventHandler()
payment_handler = PaymentEventHandler()
inventory_handler = InventoryEventHandler()
audit_handler = AuditEventHandler()

event_bus.register_handler(order_handler)
event_bus.register_handler(payment_handler)
event_bus.register_handler(inventory_handler)
event_bus.register_handler(audit_handler)


# Event middleware for logging
async def logging_middleware(event: Event) -> Event:
    logger.info(f"Event middleware: {event.name} -> {event.type.value}")
    return event

event_bus.add_middleware(logging_middleware)


# Saga for order processing
async def create_order_saga(order_id: str, items: List[Dict[str, Any]], total: float) -> bool:
    """Saga for processing a complete order"""
    
    saga = Saga("order_processing", order_id)
    
    # Step 1: Create order
    async def create_order():
        event = Event(
            type=EventType.DOMAIN,
            name="order.created",
            data={"order_id": order_id, "items": items, "total": total},
            correlation_id=order_id
        )
        await event_bus.publish(event)
        await asyncio.sleep(0.1)  # Simulate processing
    
    # Step 2: Reserve inventory
    async def reserve_inventory():
        for item in items:
            event = Event(
                type=EventType.DOMAIN,
                name="inventory.reserved",
                data={"item_id": item["id"], "quantity": item["quantity"]},
                correlation_id=order_id
            )
            await event_bus.publish(event)
        await asyncio.sleep(0.1)
    
    async def release_inventory():
        for item in items:
            event = Event(
                type=EventType.DOMAIN,
                name="inventory.released",
                data={"item_id": item["id"], "quantity": item["quantity"]},
                correlation_id=order_id
            )
            await event_bus.publish(event)
    
    # Step 3: Process payment
    async def process_payment():
        payment_id = f"pay_{order_id}"
        event = Event(
            type=EventType.DOMAIN,
            name="payment.processed",
            data={"payment_id": payment_id, "order_id": order_id, "amount": total},
            correlation_id=order_id
        )
        await event_bus.publish(event)
        await asyncio.sleep(0.1)
    
    async def refund_payment():
        payment_id = f"pay_{order_id}"
        event = Event(
            type=EventType.DOMAIN,
            name="payment.refunded",
            data={"payment_id": payment_id, "order_id": order_id, "amount": total},
            correlation_id=order_id
        )
        await event_bus.publish(event)
    
    # Step 4: Confirm order
    async def confirm_order():
        event = Event(
            type=EventType.DOMAIN,
            name="order.confirmed",
            data={"order_id": order_id},
            correlation_id=order_id
        )
        await event_bus.publish(event)
        await asyncio.sleep(0.1)
    
    # Add saga steps
    saga.add_step("create_order", create_order, None)
    saga.add_step("reserve_inventory", reserve_inventory, release_inventory)
    saga.add_step("process_payment", process_payment, refund_payment)
    saga.add_step("confirm_order", confirm_order, None)
    
    # Execute saga
    return await saga_manager.start_saga(saga)


# API Routes
@app.get("/")
async def home():
    """Home page with event-driven architecture info"""
    return {
        "message": "Event-Driven Architecture Example",
        "features": [
            "Event Bus for loose coupling",
            "Event Sourcing with event store",
            "Saga pattern for distributed transactions",
            "Event handlers and middleware",
            "Event replay and audit trails"
        ],
        "endpoints": {
            "POST /orders": "Create a new order (triggers saga)",
            "GET /orders": "List all orders",
            "GET /payments": "List all payments",
            "GET /inventory": "Show current inventory",
            "GET /audit": "Show audit log",
            "GET /events": "List all events",
            "POST /replay": "Replay events for a handler"
        }
    }


@app.post("/orders")
async def create_order(request):
    """Create a new order using saga pattern"""
    data = await request.json()
    
    order_id = data.get("order_id", f"order_{int(time.time())}")
    items = data.get("items", [])
    total = data.get("total", 0)
    
    # Start saga
    success = await create_order_saga(order_id, items, total)
    
    return {
        "order_id": order_id,
        "saga_success": success,
        "message": "Order processing saga completed" if success else "Order processing saga failed"
    }


@app.get("/orders")
async def list_orders():
    """List all orders"""
    return {
        "orders": list(order_handler.orders.values()),
        "count": len(order_handler.orders)
    }


@app.get("/payments")
async def list_payments():
    """List all payments"""
    return {
        "payments": list(payment_handler.payments.values()),
        "count": len(payment_handler.payments)
    }


@app.get("/inventory")
async def get_inventory():
    """Get current inventory levels"""
    return {
        "inventory": inventory_handler.inventory,
        "total_items": len(inventory_handler.inventory)
    }


@app.get("/audit")
async def get_audit_log():
    """Get audit log"""
    return {
        "audit_log": audit_handler.audit_log,
        "count": len(audit_handler.audit_log)
    }


@app.get("/events")
async def list_events():
    """List all events from event store"""
    events = await event_store.get_events()
    return {
        "events": [event.to_dict() for event in events],
        "count": len(events)
    }


@app.post("/replay")
async def replay_events(request):
    """Replay events for a specific handler"""
    data = await request.json()
    handler_name = data.get("handler", "order")
    
    handlers = {
        "order": order_handler,
        "payment": payment_handler,
        "inventory": inventory_handler
    }
    
    if handler_name not in handlers:
        return {"error": f"Unknown handler: {handler_name}"}
    
    handler = handlers[handler_name]
    
    # Clear handler state
    if handler_name == "order":
        handler.orders.clear()
    elif handler_name == "payment":
        handler.payments.clear()
    elif handler_name == "inventory":
        handler.inventory = {"item1": 100, "item2": 50, "item3": 75}
    
    # Replay events
    await event_store.replay_events(handler)
    
    return {
        "message": f"Events replayed for {handler_name} handler",
        "handler": handler_name
    }


@app.get("/saga/{correlation_id}")
async def get_saga_status(correlation_id: str):
    """Get saga status"""
    status = saga_manager.get_saga_status(correlation_id)
    if status:
        return status
    else:
        return {"error": f"Saga not found: {correlation_id}"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 QakeAPI Event-Driven Architecture Example running at http://localhost:8040")
    uvicorn.run(app, host="127.0.0.1", port=8040) 