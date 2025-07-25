Event-Driven Architecture Guide
==============================

QakeAPI provides a powerful event-driven architecture system that allows you to build loosely coupled, scalable applications using events and event handlers.

.. contents:: Table of Contents
   :local:

Core Concepts
-------------

Event-Driven Architecture (EDA) is a design pattern where components communicate through events rather than direct method calls. This promotes loose coupling and scalability.

Key Components:

* **Event**: A message representing something that happened
* **Event Bus**: Central component that manages event publishing and subscription
* **Event Handler**: Component that processes specific events
* **Event Store**: Persistent storage for events (optional)
* **Saga**: Pattern for managing distributed transactions

Basic Event System
-----------------

Simple event publishing and handling:

.. code-block:: python

   from qakeapi import Application
   from qakeapi.core.events import EventBus, Event

   app = Application()
   event_bus = EventBus()

   # Subscribe to events
   @event_bus.subscribe("user.created")
   async def handle_user_created(event: Event):
       print(f"New user created: {event.data}")
       # Send welcome email, create profile, etc.

   @event_bus.subscribe("user.updated")
   async def handle_user_updated(event: Event):
       print(f"User updated: {event.data}")
       # Update cache, notify other services, etc.

   # Publish events
   @app.post("/users")
   async def create_user(request):
       user_data = await request.json()
       
       # Create user in database
       user = create_user_in_db(user_data)
       
       # Publish event
       await event_bus.publish("user.created", user.dict())
       
       return {"user": user.dict()}

   @app.put("/users/{user_id}")
   async def update_user(request, user_id: int):
       user_data = await request.json()
       
       # Update user in database
       user = update_user_in_db(user_id, user_data)
       
       # Publish event
       await event_bus.publish("user.updated", user.dict())
       
       return {"user": user.dict()}

Custom Event Handlers
--------------------

Creating custom event handlers for specific business logic:

.. code-block:: python

   from qakeapi.core.events import EventHandler, Event, EventBus
   from typing import Dict, Any, Set
   import smtplib
   from email.mime.text import MIMEText

   class EmailEventHandler(EventHandler):
       def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
           self.smtp_server = smtp_server
           self.smtp_port = smtp_port
           self.username = username
           self.password = password
           self.event_names = {"user.created", "user.updated", "order.completed"}
       
       async def handle(self, event: Event) -> None:
           if event.name == "user.created":
               await self.send_welcome_email(event.data)
           elif event.name == "user.updated":
               await self.send_update_notification(event.data)
           elif event.name == "order.completed":
               await self.send_order_confirmation(event.data)
       
       async def send_welcome_email(self, user_data: Dict[str, Any]):
           subject = "Welcome to Our Platform!"
           body = f"""
           Hello {user_data['name']},
           
           Welcome to our platform! We're excited to have you on board.
           
           Best regards,
           The Team
           """
           
           await self.send_email(user_data['email'], subject, body)
       
       async def send_update_notification(self, user_data: Dict[str, Any]):
           subject = "Your Profile Has Been Updated"
           body = f"""
           Hello {user_data['name']},
           
           Your profile has been successfully updated.
           
           Best regards,
           The Team
           """
           
           await self.send_email(user_data['email'], subject, body)
       
       async def send_order_confirmation(self, order_data: Dict[str, Any]):
           subject = "Order Confirmation"
           body = f"""
           Hello {order_data['customer_name']},
           
           Your order #{order_data['order_id']} has been confirmed.
           Total: ${order_data['total']}
           
           Best regards,
           The Team
           """
           
           await self.send_email(order_data['customer_email'], subject, body)
       
       async def send_email(self, to_email: str, subject: str, body: str):
           # Implementation for sending email
           msg = MIMEText(body)
           msg['Subject'] = subject
           msg['From'] = self.username
           msg['To'] = to_email
           
           # In production, use async email library
           print(f"Sending email to {to_email}: {subject}")

   class AuditEventHandler(EventHandler):
       def __init__(self, audit_log_path: str = "audit.log"):
           self.audit_log_path = audit_log_path
           self.event_names = {"*"}  # Handle all events
       
       async def handle(self, event: Event) -> None:
           audit_entry = {
               "timestamp": event.timestamp.isoformat(),
               "event_name": event.name,
               "event_data": event.data,
               "event_type": event.event_type.value
           }
           
           # Write to audit log
           with open(self.audit_log_path, "a") as f:
               f.write(f"{audit_entry}\n")

   class NotificationEventHandler(EventHandler):
       def __init__(self, webhook_url: str):
           self.webhook_url = webhook_url
           self.event_names = {"user.created", "order.completed"}
       
       async def handle(self, event: Event) -> None:
           import httpx
           
           notification_data = {
               "event": event.name,
               "data": event.data,
               "timestamp": event.timestamp.isoformat()
           }
           
           async with httpx.AsyncClient() as client:
               await client.post(self.webhook_url, json=notification_data)

   # Register handlers with event bus
   event_bus = EventBus()
   
   email_handler = EmailEventHandler(
       smtp_server="smtp.gmail.com",
       smtp_port=587,
       username="your-email@gmail.com",
       password="your-password"
   )
   
   audit_handler = AuditEventHandler("audit.log")
   notification_handler = NotificationEventHandler("https://hooks.slack.com/...")
   
   event_bus.register_handler(email_handler)
   event_bus.register_handler(audit_handler)
   event_bus.register_handler(notification_handler)

Event Store and Event Sourcing
-----------------------------

Implementing event sourcing for audit trails and state reconstruction:

.. code-block:: python

   from qakeapi.core.events import EventStore, InMemoryEventStorage, Event
   from typing import List, Dict, Any
   import json

   class UserEventStore:
       def __init__(self, event_store: EventStore):
           self.event_store = event_store
       
       async def save_user_event(self, event: Event):
           await self.event_store.save_event(event)
       
       async def get_user_events(self, user_id: str) -> List[Event]:
           events = await self.event_store.get_events_by_aggregate_id(user_id)
           return sorted(events, key=lambda e: e.timestamp)
       
       async def reconstruct_user_state(self, user_id: str) -> Dict[str, Any]:
           events = await self.get_user_events(user_id)
           user_state = {}
           
           for event in events:
               if event.name == "user.created":
                   user_state.update(event.data)
               elif event.name == "user.updated":
                   user_state.update(event.data)
               elif event.name == "user.deleted":
                   user_state = {}
           
           return user_state

   # Initialize event store
   event_store = EventStore(InMemoryEventStorage())
   user_event_store = UserEventStore(event_store)

   @app.post("/users")
   async def create_user(request):
       user_data = await request.json()
       
       # Create user event
       event = Event(
           name="user.created",
           data=user_data,
           aggregate_id=user_data.get("email"),
           event_type=EventType.USER
       )
       
       # Save event
       await user_event_store.save_user_event(event)
       
       # Publish event
       await event_bus.publish(event.name, event.data)
       
       return {"user": user_data}

   @app.get("/users/{user_id}/history")
   async def get_user_history(user_id: str):
       events = await user_event_store.get_user_events(user_id)
       return {"events": [event.dict() for event in events]}

   @app.get("/users/{user_id}/state")
   async def get_user_state(user_id: str):
       state = await user_event_store.reconstruct_user_state(user_id)
       return {"state": state}

Saga Pattern
------------

Implementing distributed transactions using the Saga pattern:

.. code-block:: python

   from qakeapi.core.events import Saga, SagaManager, Event
   from typing import List, Dict, Any
   import asyncio

   class OrderSaga(Saga):
       def __init__(self, order_id: str):
           super().__init__(f"order_saga_{order_id}")
           self.order_id = order_id
           self.steps = [
               "validate_inventory",
               "reserve_inventory",
               "process_payment",
               "confirm_order"
           ]
           self.current_step = 0
           self.compensation_steps = []
       
       async def execute(self) -> bool:
           try:
               # Step 1: Validate inventory
               if not await self.validate_inventory():
                   return False
               
               # Step 2: Reserve inventory
               if not await self.reserve_inventory():
                   await self.compensate()
                   return False
               
               # Step 3: Process payment
               if not await self.process_payment():
                   await self.compensate()
                   return False
               
               # Step 4: Confirm order
               if not await self.confirm_order():
                   await self.compensate()
                   return False
               
               return True
           
           except Exception as e:
               await self.compensate()
               return False
       
       async def validate_inventory(self) -> bool:
           # Check if items are available
           order_data = await self.get_order_data()
           inventory_check = await self.check_inventory(order_data["items"])
           
           if inventory_check["available"]:
               self.compensation_steps.append(("release_inventory", order_data))
               return True
           return False
       
       async def reserve_inventory(self) -> bool:
           # Reserve items in inventory
           order_data = await self.get_order_data()
           reservation = await self.reserve_items(order_data["items"])
           
           if reservation["success"]:
               self.compensation_steps.append(("release_inventory", order_data))
               return True
           return False
       
       async def process_payment(self) -> bool:
           # Process payment
           order_data = await self.get_order_data()
           payment = await self.charge_payment(order_data["payment_info"])
           
           if payment["success"]:
               self.compensation_steps.append(("refund_payment", payment))
               return True
           return False
       
       async def confirm_order(self) -> bool:
           # Confirm order
           order_data = await self.get_order_data()
           confirmation = await self.confirm_order_in_db(order_data)
           
           if confirmation["success"]:
               return True
           return False
       
       async def compensate(self):
           # Execute compensation steps in reverse order
           for step_name, step_data in reversed(self.compensation_steps):
               if step_name == "release_inventory":
                   await self.release_inventory(step_data)
               elif step_name == "refund_payment":
                   await self.refund_payment(step_data)

   # Initialize saga manager
   saga_manager = SagaManager()

   @app.post("/orders")
   async def create_order(request):
       order_data = await request.json()
       
       # Create and execute saga
       saga = OrderSaga(order_data["order_id"])
       success = await saga_manager.execute_saga(saga)
       
       if success:
           # Publish success event
           await event_bus.publish("order.completed", order_data)
           return {"order": order_data, "status": "completed"}
       else:
           # Publish failure event
           await event_bus.publish("order.failed", order_data)
           return {"order": order_data, "status": "failed"}, 400

Testing Event Handlers
---------------------

Testing event handlers and event-driven functionality:

.. code-block:: python

   import pytest
   from qakeapi.core.events import EventBus, Event, EventType
   from datetime import datetime

   @pytest.mark.asyncio
   async def test_event_handler():
       event_bus = EventBus()
       events_received = []
       
       @event_bus.subscribe("test.event")
       async def test_handler(event: Event):
           events_received.append(event)
       
       # Publish event
       await event_bus.publish("test.event", {"data": "test"})
       
       # Check if handler was called
       assert len(events_received) == 1
       assert events_received[0].name == "test.event"
       assert events_received[0].data["data"] == "test"

   @pytest.mark.asyncio
   async def test_custom_event_handler():
       event_bus = EventBus()
       events_handled = []
       
       class TestEventHandler(EventHandler):
           def __init__(self):
               self.event_names = {"test.event"}
           
           async def handle(self, event: Event) -> None:
               events_handled.append(event)
       
       handler = TestEventHandler()
       event_bus.register_handler(handler)
       
       # Publish event
       await event_bus.publish("test.event", {"data": "test"})
       
       # Check if handler was called
       assert len(events_handled) == 1
       assert events_handled[0].name == "test.event"

   @pytest.mark.asyncio
   async def test_saga_execution():
       saga_manager = SagaManager()
       
       class TestSaga(Saga):
           def __init__(self):
               super().__init__("test_saga")
               self.steps_executed = []
           
           async def execute(self) -> bool:
               self.steps_executed.append("step1")
               self.steps_executed.append("step2")
               return True
       
       saga = TestSaga()
       success = await saga_manager.execute_saga(saga)
       
       assert success
       assert saga.steps_executed == ["step1", "step2"]

Event-Driven Microservices
-------------------------

Building microservices that communicate through events:

.. code-block:: python

   # User Service
   from qakeapi import Application
   from qakeapi.core.events import EventBus, Event

   user_app = Application()
   user_event_bus = EventBus()

   @user_event_bus.subscribe("order.created")
   async def handle_order_created(event: Event):
       # Update user's order history
       user_id = event.data["user_id"]
       await update_user_order_history(user_id, event.data)

   @user_app.post("/users")
   async def create_user(request):
       user_data = await request.json()
       user = await create_user_in_db(user_data)
       
       # Publish user created event
       await user_event_bus.publish("user.created", user.dict())
       
       return {"user": user.dict()}

   # Order Service
   order_app = Application()
   order_event_bus = EventBus()

   @order_event_bus.subscribe("user.created")
   async def handle_user_created(event: Event):
       # Create user's shopping cart
       user_id = event.data["id"]
       await create_user_cart(user_id)

   @order_app.post("/orders")
   async def create_order(request):
       order_data = await request.json()
       order = await create_order_in_db(order_data)
       
       # Publish order created event
       await order_event_bus.publish("order.created", order.dict())
       
       return {"order": order.dict()}

   # Inventory Service
   inventory_app = Application()
   inventory_event_bus = EventBus()

   @inventory_event_bus.subscribe("order.created")
   async def handle_order_created(event: Event):
       # Reserve inventory for order
       order_id = event.data["id"]
       items = event.data["items"]
       await reserve_inventory(order_id, items)

   @inventory_event_bus.subscribe("order.cancelled")
   async def handle_order_cancelled(event: Event):
       # Release inventory for cancelled order
       order_id = event.data["id"]
       await release_inventory(order_id)

Best Practices
--------------

1. **Event Naming**: Use descriptive, past-tense event names (e.g., "user.created", "order.completed")
2. **Event Data**: Keep event data immutable and include all necessary information
3. **Idempotency**: Make event handlers idempotent to handle duplicate events
4. **Error Handling**: Implement proper error handling and retry mechanisms
5. **Event Versioning**: Version your events to handle schema evolution
6. **Monitoring**: Monitor event processing and handler performance
7. **Testing**: Test event handlers in isolation and integration

Common Patterns
---------------

Event Sourcing with CQRS
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class UserCommandHandler:
       def __init__(self, event_store: EventStore):
           self.event_store = event_store
       
       async def create_user(self, user_data: Dict[str, Any]):
           event = Event(
               name="user.created",
               data=user_data,
               aggregate_id=user_data["email"]
           )
           await self.event_store.save_event(event)
       
       async def update_user(self, user_id: str, user_data: Dict[str, Any]):
           event = Event(
               name="user.updated",
               data=user_data,
               aggregate_id=user_id
           )
           await self.event_store.save_event(event)

   class UserQueryHandler:
       def __init__(self, event_store: EventStore):
           self.event_store = event_store
       
       async def get_user(self, user_id: str) -> Dict[str, Any]:
           events = await self.event_store.get_events_by_aggregate_id(user_id)
           return self.reconstruct_user_state(events)
       
       def reconstruct_user_state(self, events: List[Event]) -> Dict[str, Any]:
           state = {}
           for event in sorted(events, key=lambda e: e.timestamp):
               if event.name == "user.created":
                   state.update(event.data)
               elif event.name == "user.updated":
                   state.update(event.data)
           return state

Event Correlation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   class CorrelationMiddleware:
       def __init__(self, correlation_id_header: str = "X-Correlation-ID"):
           self.correlation_id_header = correlation_id_header
       
       async def __call__(self, request, handler):
           correlation_id = request.headers.get(self.correlation_id_header)
           
           if not correlation_id:
               correlation_id = str(uuid.uuid4())
           
           # Add correlation ID to request context
           request.context = {"correlation_id": correlation_id}
           
           response = await handler(request)
           
           # Add correlation ID to response headers
           response.headers[self.correlation_id_header] = correlation_id
           
           return response

   # Use in event handlers
   @event_bus.subscribe("user.created")
   async def handle_user_created(event: Event):
       correlation_id = event.metadata.get("correlation_id")
       logger.info(f"Processing user.created with correlation_id: {correlation_id}")
       
       # Process event with correlation ID for tracing
       await process_user_creation(event.data, correlation_id) 