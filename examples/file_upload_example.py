"""
Example demonstrating file upload in QakeAPI.

This example shows how to handle file uploads with validation,
storage, and security features.
"""

import sys
import io
from pathlib import Path
from qakeapi import QakeAPI, CORSMiddleware, FileUpload, IMAGE_TYPES, IMAGE_MIME_TYPES

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = QakeAPI(
    title="File Upload Example API",
    version="1.0.0",
    description="Example demonstrating file upload functionality",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Example 1: Basic file upload
@app.post("/upload")
async def upload_file(file: FileUpload):
    """
    Basic file upload endpoint.
    
    Accepts any file and saves it to uploads directory.
    """
    # Save file
    saved_path = await file.save(str(UPLOAD_DIR))
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "size": file.size,
        "content_type": file.content_type,
        "saved_path": saved_path
    }


# Example 2: Image upload with validation
@app.post("/upload/image")
async def upload_image(file: FileUpload):
    """
    Image upload with type and size validation.
    
    Only accepts image files (jpg, png, gif, etc.) up to 5MB.
    """
    # Validate file size (5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if not file.validate_size(max_size):
        return {
            "error": "File too large",
            "max_size": max_size,
            "file_size": file.size
        }, 400
    
    # Validate file type
    if not file.validate_type(IMAGE_TYPES):
        return {
            "error": "Invalid file type",
            "allowed_types": list(IMAGE_TYPES),
            "file_type": file.extension
        }, 400
    
    # Validate content type
    if not file.validate_content_type(IMAGE_MIME_TYPES):
        return {
            "error": "Invalid content type",
            "content_type": file.content_type
        }, 400
    
    # Save file with original extension
    saved_path = await file.save(str(UPLOAD_DIR / "images"))
    
    return {
        "message": "Image uploaded successfully",
        "filename": file.filename,
        "size": file.size,
        "saved_path": saved_path
    }


# Example 3: Multiple files upload
@app.post("/upload/multiple")
async def upload_multiple(request):
    """
    Upload multiple files.
    
    Uses request.files() to get all uploaded files.
    """
    files = await request.files()
    
    if not files:
        return {"error": "No files uploaded"}, 400
    
    uploaded_files = []
    for field_name, file in files.items():
        # Save each file
        saved_path = await file.save(str(UPLOAD_DIR / "multiple"))
        
        uploaded_files.append({
            "field_name": field_name,
            "filename": file.filename,
            "size": file.size,
            "saved_path": saved_path
        })
    
    return {
        "message": f"Uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    }


# Example 4: File upload with form data
@app.post("/upload/with-form")
async def upload_with_form(request):
    """
    Upload file with additional form fields.
    
    Demonstrates handling both files and form fields.
    """
    # Get both form fields and files
    data = await request.form_and_files()
    
    fields = data.get("fields", {})
    files = data.get("files", {})
    
    if "file" not in files:
        return {"error": "File is required"}, 400
    
    file = files["file"]
    description = fields.get("description", "No description")
    
    # Save file
    saved_path = await file.save(str(UPLOAD_DIR / "with-form"))
    
    return {
        "message": "File uploaded with form data",
        "filename": file.filename,
        "description": description,
        "saved_path": saved_path
    }


# Example 5: File info endpoint (no upload)
@app.get("/files")
def list_files():
    """List uploaded files."""
    files = []
    for file_path in UPLOAD_DIR.rglob("*"):
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "path": str(file_path.relative_to(UPLOAD_DIR)),
                "size": file_path.stat().st_size
            })
    
    return {
        "total_files": len(files),
        "files": files
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("QakeAPI File Upload Example")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST /upload              - Basic file upload")
    print("  POST /upload/image        - Image upload with validation")
    print("  POST /upload/multiple     - Multiple files upload")
    print("  POST /upload/with-form    - File with form data")
    print("  GET  /files               - List uploaded files")
    print("\nTry these requests:")
    print("  # Upload a file")
    print("  curl -X POST http://localhost:8000/upload \\")
    print("    -F 'file=@/path/to/file.txt'")
    print("\n  # Upload an image")
    print("  curl -X POST http://localhost:8000/upload/image \\")
    print("    -F 'file=@/path/to/image.jpg'")
    print("\n  # Upload with form data")
    print("  curl -X POST http://localhost:8000/upload/with-form \\")
    print("    -F 'file=@/path/to/file.txt' \\")
    print("    -F 'description=My file'")
    print("\nSwagger UI: http://localhost:8000/docs")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

