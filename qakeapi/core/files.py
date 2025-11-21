import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncIterator, BinaryIO, Dict, Optional


class UploadFile:
    """Uploaded file handler"""

    def __init__(
        self,
        filename: str,
        content_type: str = "application/octet-stream",
        headers: Optional[Dict[str, str]] = None,
    ):
        self.filename = filename
        self.content_type = content_type
        self.headers = headers or {}
        self._file: Optional[BinaryIO] = None
        self._temp_file = tempfile.NamedTemporaryFile(delete=False)

    async def write(self, data: bytes) -> None:
        """Write data to file"""
        self._temp_file.write(data)
        self._temp_file.flush()

    async def read(self, size: int = -1) -> bytes:
        """Read data from file"""
        if self._file is None:
            self._temp_file.seek(0)
            self._file = self._temp_file
        return self._file.read(size)

    async def seek(self, offset: int) -> None:
        """Seek to position in file"""
        if self._file is None:
            self._temp_file.seek(0)
            self._file = self._temp_file
        self._file.seek(offset)

    async def close(self) -> None:
        """Close and cleanup file"""
        if self._file is not None:
            self._file.close()
        self._temp_file.close()
        try:
            os.unlink(self._temp_file.name)
        except OSError:
            pass

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate over file contents"""
        chunk_size = 8192  # 8KB chunks
        await self.seek(0)
        while True:
            chunk = await self.read(chunk_size)
            if not chunk:
                break
            yield chunk

    async def save(self, path: str) -> None:
        """Save file to disk"""
        await self.seek(0)
        with open(path, "wb") as f:
            while True:
                chunk = await self.read(8192)
                if not chunk:
                    break
                f.write(chunk)

    async def __aenter__(self):
        """Async context manager enter"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_file.close()
        try:
            os.unlink(self._temp_file.name)
        except OSError:
            pass
