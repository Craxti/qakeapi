"""
File upload handling for QakeAPI.

Provides file upload functionality with validation, storage, and security features.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Set
from io import BytesIO


class FileUpload:
    """
    Represents an uploaded file.
    
    Provides access to file data, metadata, and utilities for saving files.
    """
    
    def __init__(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize file upload.
        
        Args:
            filename: Original filename
            content: File content as bytes
            content_type: MIME type (e.g., 'image/jpeg')
            headers: Additional headers from multipart form
        """
        self.filename = filename
        self.content = content
        self.content_type = content_type or "application/octet-stream"
        self.headers = headers or {}
        self._size = len(content)
    
    @property
    def size(self) -> int:
        """File size in bytes."""
        return self._size
    
    @property
    def extension(self) -> str:
        """File extension (without dot)."""
        return Path(self.filename).suffix.lstrip(".")
    
    @property
    def name(self) -> str:
        """File name without extension."""
        return Path(self.filename).stem
    
    def read(self) -> bytes:
        """Read file content."""
        return self.content
    
    def read_text(self, encoding: str = "utf-8") -> str:
        """Read file content as text."""
        return self.content.decode(encoding)
    
    async def save(
        self,
        destination: str,
        filename: Optional[str] = None,
        create_dirs: bool = True,
    ) -> str:
        """
        Save file to disk.
        
        Args:
            destination: Directory path or full file path
            filename: Optional filename (uses original if not provided)
            create_dirs: Create directories if they don't exist
            
        Returns:
            Full path to saved file
        """
        dest_path = Path(destination)
        
        # If destination is a directory, append filename
        if dest_path.is_dir() or (not dest_path.exists() and not dest_path.suffix):
            if filename:
                dest_path = dest_path / filename
            else:
                dest_path = dest_path / self.filename
        
        # Create directories if needed
        if create_dirs:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        dest_path.write_bytes(self.content)
        
        return str(dest_path.absolute())
    
    def save_to_temp(self, suffix: Optional[str] = None) -> str:
        """
        Save file to temporary location.
        
        Args:
            suffix: Optional file suffix (extension)
            
        Returns:
            Path to temporary file
        """
        if suffix and not suffix.startswith("."):
            suffix = "." + suffix
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(self.content)
            return tmp.name
    
    def validate_size(self, max_size: int) -> bool:
        """
        Validate file size.
        
        Args:
            max_size: Maximum size in bytes
            
        Returns:
            True if file size is valid
        """
        return self.size <= max_size
    
    def validate_type(self, allowed_types: Set[str]) -> bool:
        """
        Validate file type by extension.
        
        Args:
            allowed_types: Set of allowed extensions (e.g., {'jpg', 'png', 'pdf'})
            
        Returns:
            True if file type is allowed
        """
        return self.extension.lower() in {ext.lower().lstrip(".") for ext in allowed_types}
    
    def validate_content_type(self, allowed_types: Set[str]) -> bool:
        """
        Validate file MIME type.
        
        Args:
            allowed_types: Set of allowed MIME types (e.g., {'image/jpeg', 'image/png'})
            
        Returns:
            True if content type is allowed
        """
        return self.content_type.lower() in {ct.lower() for ct in allowed_types}
    
    def __repr__(self) -> str:
        return f"FileUpload(filename={self.filename!r}, size={self.size}, type={self.content_type!r})"


class MultipartParser:
    """
    Parser for multipart/form-data requests.
    
    Handles file uploads and form fields from multipart requests.
    """
    
    def __init__(self, boundary: str):
        """
        Initialize multipart parser.
        
        Args:
            boundary: Multipart boundary string
        """
        self.boundary = boundary.encode()
        self.boundary_start = b"--" + self.boundary
        self.boundary_end = self.boundary_start + b"--"
    
    def parse(self, body: bytes) -> Dict[str, Any]:
        """
        Parse multipart body.
        
        Args:
            body: Raw request body
            
        Returns:
            Dictionary with form fields and files
            {
                'fields': {'field_name': 'value'},
                'files': {'file_name': FileUpload}
            }
        """
        if not body.startswith(self.boundary_start):
            return {"fields": {}, "files": {}}
        
        parts = body.split(self.boundary_start)[1:]
        if parts and parts[-1].endswith(self.boundary_end):
            parts[-1] = parts[-1][:-len(self.boundary_end)]
        
        fields: Dict[str, Any] = {}
        files: Dict[str, FileUpload] = {}
        
        for part in parts:
            if not part.strip():
                continue
            
            # Split headers and content
            if b"\r\n\r\n" not in part:
                continue
            
            header_part, content = part.split(b"\r\n\r\n", 1)
            content = content.rstrip(b"\r\n")
            
            # Parse headers
            headers = self._parse_headers(header_part)
            
            # Extract field name and filename
            content_disposition = headers.get("content-disposition", "")
            field_name = self._extract_field_name(content_disposition)
            
            if not field_name:
                continue
            
            # Check if it's a file
            filename = self._extract_filename(content_disposition)
            content_type = headers.get("content-type", "application/octet-stream")
            
            if filename:
                # It's a file upload
                files[field_name] = FileUpload(
                    filename=filename,
                    content=content,
                    content_type=content_type,
                    headers=headers,
                )
            else:
                # It's a regular form field
                fields[field_name] = content.decode("utf-8", errors="replace")
        
        return {"fields": fields, "files": files}
    
    def _parse_headers(self, header_part: bytes) -> Dict[str, str]:
        """Parse headers from multipart part."""
        headers: Dict[str, str] = {}
        
        for line in header_part.split(b"\r\n"):
            if b":" not in line:
                continue
            
            key, value = line.split(b":", 1)
            key = key.strip().decode("utf-8", errors="replace").lower()
            value = value.strip().decode("utf-8", errors="replace")
            headers[key] = value
        
        return headers
    
    def _extract_field_name(self, content_disposition: str) -> Optional[str]:
        """Extract field name from Content-Disposition header."""
        if "name=" not in content_disposition:
            return None
        
        # Extract name="field_name" or name='field_name'
        start = content_disposition.find("name=") + 5
        quote_char = content_disposition[start] if start < len(content_disposition) else '"'
        
        if quote_char in ('"', "'"):
            start += 1
            end = content_disposition.find(quote_char, start)
        else:
            # No quotes, find semicolon or end
            end = len(content_disposition)
            for char in (";", " "):
                idx = content_disposition.find(char, start)
                if idx != -1:
                    end = min(end, idx)
        
        return content_disposition[start:end].strip()
    
    def _extract_filename(self, content_disposition: str) -> Optional[str]:
        """Extract filename from Content-Disposition header."""
        if "filename=" not in content_disposition:
            return None
        
        # Extract filename="file.txt" or filename='file.txt'
        start = content_disposition.find("filename=") + 9
        quote_char = content_disposition[start] if start < len(content_disposition) else '"'
        
        if quote_char in ('"', "'"):
            start += 1
            end = content_disposition.find(quote_char, start)
        else:
            # No quotes, find semicolon or end
            end = len(content_disposition)
            for char in (";", " "):
                idx = content_disposition.find(char, start)
                if idx != -1:
                    end = min(end, idx)
        
        filename = content_disposition[start:end].strip()
        
        # Remove path if present (security)
        return os.path.basename(filename) if filename else None


def parse_multipart(body: bytes, content_type: str) -> Dict[str, Any]:
    """
    Parse multipart/form-data request body.
    
    Args:
        body: Raw request body
        content_type: Content-Type header value
        
    Returns:
        Dictionary with 'fields' and 'files' keys
        
    Raises:
        ValueError: If content type is not multipart or boundary is missing
    """
    if not content_type.startswith("multipart/form-data"):
        raise ValueError("Content-Type must be multipart/form-data")
    
    # Extract boundary
    if "boundary=" not in content_type:
        raise ValueError("Missing boundary in Content-Type header")
    
    boundary = content_type.split("boundary=")[1].strip().strip('"').strip("'")
    
    parser = MultipartParser(boundary)
    return parser.parse(body)


# Common file type validators
IMAGE_TYPES = {"jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"}
DOCUMENT_TYPES = {"pdf", "doc", "docx", "xls", "xlsx", "txt", "csv"}
VIDEO_TYPES = {"mp4", "avi", "mov", "wmv", "flv", "webm"}
AUDIO_TYPES = {"mp3", "wav", "ogg", "flac", "aac"}

IMAGE_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif",
    "image/webp", "image/svg+xml", "image/bmp"
}

DOCUMENT_MIME_TYPES = {
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv"
}

