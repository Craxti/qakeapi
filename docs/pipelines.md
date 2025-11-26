# Pipelines

QakeAPI supports function pipelines for composing complex processing workflows.

## Basic Pipeline

Create a pipeline of processing steps:

```python
from qakeapi import QakeAPI

app = QakeAPI()

def authenticate(request):
    """Step 1: Authenticate user."""
    token = request.headers.get("Authorization")
    if not token:
        raise ValueError("Unauthorized")
    return {"user_id": 1, "token": token}

def authorize(data):
    """Step 2: Check permissions."""
    if data["user_id"] != 1:
        raise ValueError("Forbidden")
    return data

def validate(data):
    """Step 3: Validate data."""
    if "name" not in data:
        raise ValueError("Name required")
    return data

def save(data):
    """Step 4: Save to database."""
    return {"id": 1, "saved": True}

@app.pipeline([authenticate, authorize, validate, save])
def create_resource(request):
    """Pipeline executes all steps in sequence."""
    return {"status": "created"}
```

## Pipeline Execution

Pipelines execute steps sequentially, passing data from one step to the next:

```python
def step1(data):
    return {"step1": "done", **data}

def step2(data):
    return {"step2": "done", **data}

def step3(data):
    return {"step3": "done", **data}

@app.pipeline([step1, step2, step3])
def process(data):
    """Each step receives output from previous step."""
    return data
```

## Error Handling

Handle errors in pipeline steps:

```python
def validate(data):
    if not data.get("email"):
        raise ValueError("Email required")
    return data

@app.pipeline([validate, save])
def create_user(data):
    try:
        return {"status": "created"}
    except ValueError as e:
        return {"error": str(e)}, 400
```

## Async Steps

Pipeline steps can be async:

```python
async def fetch_user_data(user_id):
    # Async operation
    return await database.get_user(user_id)

async def send_notification(user_data):
    # Async operation
    await email_service.send(user_data["email"])

@app.pipeline([fetch_user_data, send_notification])
async def process_user(user_id):
    """Async steps execute sequentially."""
    return {"processed": True}
```

## Mixed Sync/Async

Mix sync and async steps:

```python
def validate(data):
    # Sync validation
    if not data.get("name"):
        raise ValueError("Name required")
    return data

async def save(data):
    # Async save
    await database.save(data)
    return data

@app.pipeline([validate, save])
async def create(data):
    """Sync and async steps work together."""
    return {"created": True}
```

## Conditional Steps

Skip steps based on conditions:

```python
def should_process(data):
    return data.get("process", False)

def process_step(data):
    if not should_process(data):
        return data  # Skip processing
    # Process data
    return {"processed": True, **data}

@app.pipeline([process_step, save])
def handle(data):
    return data
```

## Use Cases

### 1. Request Processing

```python
@app.pipeline([
    authenticate,
    authorize,
    validate_request,
    transform_data,
    save_to_db
])
def create_item(request):
    return {"status": "created"}
```

### 2. Data Transformation

```python
@app.pipeline([
    fetch_raw_data,
    clean_data,
    transform_format,
    validate_schema,
    save_transformed
])
def process_data(source):
    return {"processed": True}
```

### 3. Multi-Step Validation

```python
@app.pipeline([
    validate_format,
    validate_content,
    validate_business_rules,
    check_permissions
])
def validate_complete(data):
    return {"valid": True}
```

## Best Practices

1. **Keep steps focused** - each step should do one thing
2. **Handle errors** - validate and handle errors at each step
3. **Use type hints** - helps with data flow understanding
4. **Document steps** - explain what each step does
5. **Test steps independently** - easier to debug and test


