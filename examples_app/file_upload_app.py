# -*- coding: utf-8 -*-
"""
File upload example with QakeAPI.
"""
import sys
import os
import hashlib
import mimetypes
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="File Upload Example",
    version="1.0.3",
    description="File upload functionality example with QakeAPI"
)

# Pydantic models
class FileInfo(RequestModel):
    """File information model"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size: int = Field(..., description="File size in bytes")
    hash: str = Field(..., description="File hash")

# File storage configuration
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.csv', '.json', '.xml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

# File metadata storage
files_db = {}
file_counter = 0

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

def calculate_file_hash(data: bytes) -> str:
    """Calculate SHA-256 hash of file data"""
    return hashlib.sha256(data).hexdigest()

def get_file_info(file_path: Path) -> Dict:
    """Get file information"""
    stat = file_path.stat()
    return {
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_ctime),
        "modified_at": datetime.fromtimestamp(stat.st_mtime)
    }

def save_file(file_data: bytes, filename: str) -> str:
    """Save file to disk and return unique filename"""
    # Generate unique filename
    file_id = str(uuid.uuid4())
    extension = get_file_extension(filename)
    unique_filename = f"{file_id}{extension}"
    
    # Save file
    file_path = UPLOAD_DIR / unique_filename
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    return unique_filename

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "File Upload API is running",
        "upload_directory": str(UPLOAD_DIR),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "max_file_size": f"{MAX_FILE_SIZE / (1024*1024):.1f}MB",
        "total_files": len(files_db),
        "endpoints": {
            "/upload": "POST - Upload file",
            "/files": "GET - List all files",
            "/files/{file_id}": "GET - Get file info",
            "/files/{file_id}/download": "GET - Download file",
            "/files/{file_id}": "DELETE - Delete file",
            "/stats": "GET - Upload statistics"
        }
    }

@app.post("/upload")
async def upload_file(request: Request):
    """Upload file endpoint"""
    global file_counter
    
    try:
        # Check if request has file data
        if not request.body:
            return Response.json(
                {"error": "No file data provided"},
                status_code=400
            )
        
        # Get file information from headers
        content_type = request.headers.get("Content-Type", "")
        filename = request.headers.get("X-Filename", "unknown")
        
        # Check file size
        if len(request.body) > MAX_FILE_SIZE:
            return Response.json(
                {"error": f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB"},
                status_code=413
            )
        
        # Check file extension
        if not is_allowed_file(filename):
            return Response.json(
                {"error": f"File type not allowed. Allowed types: {list(ALLOWED_EXTENSIONS)}"},
                status_code=400
            )
        
        # Calculate file hash
        file_hash = calculate_file_hash(request.body)
        
        # Check for duplicate files
        for file_id, file_info in files_db.items():
            if file_info["hash"] == file_hash:
                return Response.json(
                    {"error": "File already exists", "existing_file_id": file_id},
                    status_code=409
                )
        
        # Save file
        unique_filename = save_file(request.body, filename)
        
        # Create file record
        file_counter += 1
        file_id = str(file_counter)
        
        file_info = {
            "id": file_id,
            "original_filename": filename,
            "stored_filename": unique_filename,
            "content_type": content_type,
            "size": len(request.body),
            "hash": file_hash,
            "uploaded_at": datetime.utcnow(),
            "file_path": str(UPLOAD_DIR / unique_filename)
        }
        
        files_db[file_id] = file_info
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": filename,
            "size": len(request.body),
            "hash": file_hash
        }
        
    except Exception as e:
        return Response.json(
            {"error": f"Upload failed: {str(e)}"},
            status_code=500
        )

@app.get("/files")
async def list_files(request: Request):
    """List all uploaded files"""
    file_list = []
    for file_id, file_info in files_db.items():
        file_list.append({
            "id": file_id,
            "filename": file_info["original_filename"],
            "content_type": file_info["content_type"],
            "size": file_info["size"],
            "uploaded_at": file_info["uploaded_at"].isoformat(),
            "hash": file_info["hash"][:16] + "..."  # Truncate hash for display
        })
    
    return {
        "files": file_list,
        "total": len(files_db),
        "total_size": sum(f["size"] for f in files_db.values())
    }

@app.get("/files/{file_id}")
async def get_file_info(request: Request, file_id: str):
    """Get file information"""
    if file_id not in files_db:
        return Response.json(
            {"error": "File not found"},
            status_code=404
        )
    
    file_info = files_db[file_id]
    
    # Check if file still exists on disk
    file_path = Path(file_info["file_path"])
    if not file_path.exists():
        return Response.json(
            {"error": "File not found on disk"},
            status_code=404
        )
    
    # Get additional file info
    disk_info = get_file_info(file_path)
    
    return {
        "id": file_info["id"],
        "filename": file_info["original_filename"],
        "content_type": file_info["content_type"],
        "size": file_info["size"],
        "hash": file_info["hash"],
        "uploaded_at": file_info["uploaded_at"].isoformat(),
        "created_at": disk_info["created_at"].isoformat(),
        "modified_at": disk_info["modified_at"].isoformat(),
        "download_url": f"/files/{file_id}/download"
    }

@app.get("/files/{file_id}/download")
async def download_file(request: Request, file_id: str):
    """Download file"""
    if file_id not in files_db:
        return Response.json(
            {"error": "File not found"},
            status_code=404
        )
    
    file_info = files_db[file_id]
    file_path = Path(file_info["file_path"])
    
    if not file_path.exists():
        return Response.json(
            {"error": "File not found on disk"},
            status_code=404
        )
    
    # Read file data
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Set response headers for download
    headers = {
        "Content-Disposition": f"attachment; filename=\"{file_info['original_filename']}\"",
        "Content-Type": file_info["content_type"],
        "Content-Length": str(len(file_data))
    }
    
    return Response(
        body=file_data,
        headers=headers,
        status_code=200
    )

@app.delete("/files/{file_id}")
async def delete_file(request: Request, file_id: str):
    """Delete file"""
    if file_id not in files_db:
        return Response.json(
            {"error": "File not found"},
            status_code=404
        )
    
    file_info = files_db[file_id]
    file_path = Path(file_info["file_path"])
    
    # Delete file from disk
    if file_path.exists():
        file_path.unlink()
    
    # Remove from database
    del files_db[file_id]
    
    return {
        "message": "File deleted successfully",
        "file_id": file_id,
        "filename": file_info["original_filename"]
    }

@app.get("/stats")
async def get_upload_stats(request: Request):
    """Get upload statistics"""
    if not files_db:
        return {
            "message": "No files uploaded yet",
            "total_files": 0,
            "total_size": 0
        }
    
    total_size = sum(f["size"] for f in files_db.values())
    
    # Group by content type
    content_types = {}
    for file_info in files_db.values():
        content_type = file_info["content_type"]
        if content_type not in content_types:
            content_types[content_type] = {"count": 0, "total_size": 0}
        content_types[content_type]["count"] += 1
        content_types[content_type]["total_size"] += file_info["size"]
    
    # Get recent uploads
    recent_uploads = sorted(
        files_db.values(),
        key=lambda x: x["uploaded_at"],
        reverse=True
    )[:5]
    
    return {
        "message": "Upload statistics",
        "total_files": len(files_db),
        "total_size": total_size,
        "total_size_mb": f"{total_size / (1024*1024):.2f}MB",
        "content_types": content_types,
        "recent_uploads": [
            {
                "id": f["id"],
                "filename": f["original_filename"],
                "size": f["size"],
                "uploaded_at": f["uploaded_at"].isoformat()
            }
            for f in recent_uploads
        ]
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    # Check upload directory
    upload_dir_exists = UPLOAD_DIR.exists()
    upload_dir_writable = os.access(UPLOAD_DIR, os.W_OK)
    
    return {
        "status": "healthy" if upload_dir_exists and upload_dir_writable else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "upload_directory": {
            "exists": upload_dir_exists,
            "writable": upload_dir_writable,
            "path": str(UPLOAD_DIR)
        },
        "total_files": len(files_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8007) 