# File Upload

QakeAPI provides comprehensive file upload functionality with validation, security, and storage utilities.

## Basic Usage

### Simple File Upload

```python
from qakeapi import QakeAPI, FileUpload

@app.post("/upload")
async def upload_file(file: FileUpload):
    # Save file
    saved_path = await file.save("uploads/")
    
    return {
        "filename": file.filename,
        "size": file.size,
        "saved_path": saved_path
    }
```

The `FileUpload` type is automatically extracted from multipart/form-data requests.

## FileUpload Class

### Properties

- `filename`: Original filename
- `content`: File content as bytes
- `content_type`: MIME type (e.g., 'image/jpeg')
- `size`: File size in bytes
- `extension`: File extension (without dot)
- `name`: File name without extension

### Methods

#### `read() -> bytes`
Read file content.

#### `read_text(encoding: str = "utf-8") -> str`
Read file content as text.

#### `save(destination: str, filename: Optional[str] = None, create_dirs: bool = True) -> str`
Save file to disk.

```python
# Save to directory (uses original filename)
path = await file.save("uploads/")

# Save with custom filename
path = await file.save("uploads/", filename="custom.txt")

# Save to specific path
path = await file.save("uploads/custom.txt")
```

#### `save_to_temp(suffix: Optional[str] = None) -> str`
Save file to temporary location.

```python
temp_path = file.save_to_temp()
# File is saved to temporary location
# Remember to delete it when done
```

#### `validate_size(max_size: int) -> bool`
Validate file size.

```python
if not file.validate_size(5 * 1024 * 1024):  # 5MB
    return {"error": "File too large"}, 400
```

#### `validate_type(allowed_types: Set[str]) -> bool`
Validate file type by extension.

```python
if not file.validate_type({"jpg", "png", "gif"}):
    return {"error": "Invalid file type"}, 400
```

#### `validate_content_type(allowed_types: Set[str]) -> bool`
Validate file MIME type.

```python
if not file.validate_content_type({"image/jpeg", "image/png"}):
    return {"error": "Invalid content type"}, 400
```

## Validation Examples

### Image Upload with Validation

```python
from qakeapi import QakeAPI, FileUpload, IMAGE_TYPES, IMAGE_MIME_TYPES

@app.post("/upload/image")
async def upload_image(file: FileUpload):
    # Validate size (5MB)
    max_size = 5 * 1024 * 1024
    if not file.validate_size(max_size):
        return {"error": "File too large"}, 400
    
    # Validate file type
    if not file.validate_type(IMAGE_TYPES):
        return {"error": "Only images allowed"}, 400
    
    # Validate content type
    if not file.validate_content_type(IMAGE_MIME_TYPES):
        return {"error": "Invalid content type"}, 400
    
    # Save file
    saved_path = await file.save("uploads/images/")
    
    return {"message": "Image uploaded", "path": saved_path}
```

### Document Upload

```python
from qakeapi import QakeAPI, FileUpload, DOCUMENT_TYPES

@app.post("/upload/document")
async def upload_document(file: FileUpload):
    # Validate document type
    if not file.validate_type(DOCUMENT_TYPES):
        return {"error": "Only documents allowed"}, 400
    
    # Validate size (10MB)
    if not file.validate_size(10 * 1024 * 1024):
        return {"error": "File too large"}, 400
    
    saved_path = await file.save("uploads/documents/")
    return {"path": saved_path}
```

## Multiple Files

### Upload Multiple Files

```python
@app.post("/upload/multiple")
async def upload_multiple(request):
    files = await request.files()
    
    uploaded = []
    for field_name, file in files.items():
        path = await file.save("uploads/")
        uploaded.append({
            "field": field_name,
            "filename": file.filename,
            "path": path
        })
    
    return {"uploaded": uploaded}
```

## Form Data with Files

### Upload File with Form Fields

```python
@app.post("/upload/with-form")
async def upload_with_form(request):
    # Get both form fields and files
    data = await request.form_and_files()
    
    fields = data.get("fields", {})
    files = data.get("files", {})
    
    file = files.get("file")
    description = fields.get("description", "")
    
    if not file:
        return {"error": "File required"}, 400
    
    saved_path = await file.save("uploads/")
    
    return {
        "filename": file.filename,
        "description": description,
        "path": saved_path
    }
```

## Request Methods

### `request.files() -> Dict[str, FileUpload]`
Get all uploaded files from multipart request.

```python
files = await request.files()
file = files.get("myfile")
```

### `request.form_and_files() -> Dict[str, Any]`
Get both form fields and files.

```python
data = await request.form_and_files()
fields = data["fields"]  # Dict[str, str]
files = data["files"]     # Dict[str, FileUpload]
```

### `request.get_file(field_name: str) -> Optional[FileUpload]`
Get file by field name (synchronous, requires files() to be called first).

```python
await request.files()  # Parse first
file = request.get_file("myfile")
```

## Predefined File Types

QakeAPI provides predefined sets for common file types:

### Image Types
```python
from qakeapi import IMAGE_TYPES, IMAGE_MIME_TYPES

# Extensions: {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'}
# MIME types: {'image/jpeg', 'image/png', 'image/gif', ...}
```

### Document Types
```python
from qakeapi import DOCUMENT_TYPES, DOCUMENT_MIME_TYPES

# Extensions: {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'}
# MIME types: {'application/pdf', 'application/msword', ...}
```

## Security Considerations

1. **Validate file types** - Always validate file extensions and MIME types
2. **Limit file size** - Set maximum file size limits
3. **Sanitize filenames** - Use `os.path.basename()` to prevent path traversal
4. **Store safely** - Save files outside web root or use secure storage
5. **Scan for malware** - Consider virus scanning for uploaded files

### Example: Secure File Upload

```python
import os
from pathlib import Path
from qakeapi import QakeAPI, FileUpload, IMAGE_TYPES

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload/secure")
async def secure_upload(file: FileUpload):
    # Validate type
    if not file.validate_type(IMAGE_TYPES):
        return {"error": "Only images"}, 400
    
    # Validate size (2MB)
    if not file.validate_size(2 * 1024 * 1024):
        return {"error": "File too large"}, 400
    
    # Sanitize filename
    safe_filename = os.path.basename(file.filename)
    
    # Generate unique filename to prevent overwrites
    import uuid
    unique_name = f"{uuid.uuid4()}_{safe_filename}"
    
    # Save to secure location
    saved_path = await file.save(str(UPLOAD_DIR), filename=unique_name)
    
    return {"path": saved_path}
```

## Error Handling

File upload errors are automatically handled:

```python
@app.post("/upload")
async def upload_file(file: FileUpload):
    try:
        # File is automatically extracted and validated
        path = await file.save("uploads/")
        return {"path": path}
    except Exception as e:
        return {"error": str(e)}, 500
```

## Complete Example

```python
from qakeapi import QakeAPI, CORSMiddleware, FileUpload, IMAGE_TYPES

app = QakeAPI(title="File Upload API", version="1.0.0")
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

@app.post("/upload")
async def upload(file: FileUpload):
    # Validate
    if not file.validate_type(IMAGE_TYPES):
        return {"error": "Only images"}, 400
    
    if not file.validate_size(5 * 1024 * 1024):
        return {"error": "File too large"}, 400
    
    # Save
    path = await file.save("uploads/")
    
    return {
        "filename": file.filename,
        "size": file.size,
        "path": path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing File Uploads

```python
import pytest
from qakeapi.testing import TestClient

def test_file_upload():
    client = TestClient(app)
    
    with open("test.jpg", "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("test.jpg", f, "image/jpeg")}
        )
    
    assert response.status_code == 200
    assert "path" in response.json()
```

