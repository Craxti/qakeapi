"""
Static files serving.

This module provides functionality for serving static files.
"""

import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

from qakeapi.core.exceptions import NotFound
from qakeapi.core.request import Request
from qakeapi.core.response import FileResponse, Response


class StaticFiles:
    """
    Static files handler.

    Serves static files from a directory.
    """

    def __init__(self, directory: str, path: str = "/static"):
        """
        Initialize static files handler.

        Args:
            directory: Directory containing static files
            path: URL path prefix
        """
        self.directory = Path(directory).resolve()
        self.path = path.rstrip("/")

        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not self.directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

    def get_file_path(self, file_path: str) -> Optional[Path]:
        """
        Get full file path for requested file.

        Args:
            file_path: Requested file path

        Returns:
            Full file path or None if not found
        """
        # Remove path prefix
        if file_path.startswith(self.path):
            file_path = file_path[len(self.path) :]

        # Remove leading slash
        file_path = file_path.lstrip("/")

        # Build full path
        full_path = self.directory / file_path

        # Resolve to prevent directory traversal
        try:
            resolved = full_path.resolve()
            if not str(resolved).startswith(str(self.directory)):
                return None  # Directory traversal attempt
        except (ValueError, OSError):
            return None

        # Check if file exists and is within directory
        if not resolved.exists() or not resolved.is_file():
            return None

        return resolved

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        """
        ASGI application interface.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        path = scope.get("path", "/")
        file_path = self.get_file_path(path)

        if file_path is None:
            response = Response(
                content="File not found",
                status_code=404,
            )
            await response(scope, receive, send)
            return

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        # Get filename
        filename = file_path.name

        # Create file response
        try:
            response = FileResponse(
                path=str(file_path),
                filename=filename,
                media_type=mime_type,
            )
            await response(scope, receive, send)
        except FileNotFoundError:
            response = Response(
                content="File not found",
                status_code=404,
            )
            await response(scope, receive, send)


def mount_static(app: Any, path: str, directory: str) -> None:
    """
    Mount static files directory.

    Args:
        app: Application instance
        path: URL path prefix
        directory: Directory containing static files
    """
    static_files = StaticFiles(directory, path)

    # Add route for static files
    @app.get(f"{path}/{{file_path:path}}")
    async def serve_static(request: Request):
        """Serve static file."""
        file_path = request.get_path_param("file_path")
        full_path = static_files.get_file_path(f"{path}/{file_path}")

        if full_path is None:
            raise NotFound(f"File not found: {file_path}")

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type=mime_type,
        )
