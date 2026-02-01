# Reactive System

QakeAPI includes a reactive event system that allows you to build event-driven applications.

**Why QakeAPI events:** Built-in `emit`/`react` — no Celery, Redis, or Kafka for simple flows. In-process event bus; zero network latency. Decouple handlers (email, analytics, inventory) from request handlers. For high-scale pub/sub, add Redis later; for most APIs, in-process is enough and faster.

## Event Emitting

Emit events from anywhere in your application:

```python
from qakeapi import QakeAPI

app = QakeAPI()

@app.post("/orders")
async def create_order(request):
    data = await request.json()
    order = create_order_in_db(data)
    
    # Emit event
    await app.emit("order:created", {
        "order_id": order.id,
        "user_id": order.user_id,
        "items": order.items
    })
    
    return {"order_id": order.id}
```

## Event Reactors

React to events using decorators:

```python
@app.react("order:created")
async def on_order_created(event):
    """React to order creation event."""
    order_data = event.data
    
    # Send confirmation email
    await send_email(order_data["user_id"], "Order created")
    
    # Update inventory
    await update_inventory(order_data["items"])
    
    # Schedule shipping
    await schedule_shipping(order_data["order_id"])
```

## Multiple Reactors

Multiple reactors can listen to the same event:

```python
@app.react("order:created")
async def send_confirmation_email(event):
    await send_email(event.data["user_id"])

@app.react("order:created")
async def update_analytics(event):
    await analytics.track("order_created", event.data)

@app.react("order:created")
async def notify_admin(event):
    await notify_admin_panel(event.data)
```

## Event Data

Access event data:

```python
@app.react("user:registered")
async def on_user_registered(event):
    user_data = event.data
    
    # event.data contains the data passed to emit()
    user_id = user_data.get("user_id")
    email = user_data.get("email")
    
    # Process event
    await create_user_profile(user_id)
    await send_welcome_email(email)
```

## Event Namespacing

Use namespaces for better organization:

```python
# Order events
await app.emit("order:created", data)
await app.emit("order:paid", data)
await app.emit("order:shipped", data)

# User events
await app.emit("user:registered", data)
await app.emit("user:logged_in", data)
await app.emit("user:updated", data)

# React to namespaced events
@app.react("order:*")
async def handle_all_order_events(event):
    """React to all order events."""
    pass
```

## Synchronous Reactors

Reactors can be synchronous:

```python
@app.react("order:created")
def on_order_created_sync(event):
    """Synchronous reactor - automatically converted to async."""
    # This will run in thread pool
    log_to_file(event.data)
    update_cache(event.data)
```

## Error Handling in Reactors

Handle errors in reactors:

```python
@app.react("order:created")
async def on_order_created(event):
    try:
        await process_order(event.data)
    except Exception as e:
        # Log error but don't break the event chain
        logger.error(f"Error processing order: {e}")
        # Optionally emit error event
        await app.emit("order:processing_error", {"error": str(e)})
```

## Use Cases

### 1. Email Notifications

```python
@app.react("user:registered")
async def send_welcome_email(event):
    await email_service.send_welcome(event.data["email"])

@app.react("order:completed")
async def send_order_confirmation(event):
    await email_service.send_confirmation(event.data)
```

### 2. Database Updates

```python
@app.react("order:created")
async def update_inventory(event):
    for item in event.data["items"]:
        await inventory.decrement(item["product_id"], item["quantity"])
```

### 3. Analytics

```python
@app.react("user:action")
async def track_analytics(event):
    await analytics.track(event.data["action"], event.data)
```

### 4. Cache Invalidation

```python
@app.react("user:updated")
async def invalidate_cache(event):
    await cache.delete(f"user:{event.data['user_id']}")
```

## Best Practices

1. **Use descriptive event names** with namespaces
2. **Keep reactors focused** - one responsibility per reactor
3. **Handle errors gracefully** - don't let one reactor break others
4. **Use async** for I/O operations in reactors
5. **Document events** - document what data each event contains


