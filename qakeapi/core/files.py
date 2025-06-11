from typing import BinaryIO, Optional
import os
import tempfile
import shutil
from pathlib import Path

class UploadFile:
    """Класс для работы с загруженными файлами"""
    
    def __init__(
        self,
        filename: str,
        file: BinaryIO = None,
        content_type: str = "",
        headers: Optional[dict] = None
    ):
        self.filename = filename
        self.content_type = content_type
        self.headers = headers or {}
        self._file = file if file else tempfile.SpooledTemporaryFile(max_size=1024 * 1024)
        self._chunk_size = 8192  # 8KB chunks for iteration
        
    async def write(self, data: bytes) -> None:
        """Записать данные в файл"""
        self._file.write(data)
        self._file.flush()  # Ensure data is written
        
    async def read(self, size: int = -1) -> bytes:
        """Прочитать данные из файла"""
        # Сохраняем текущую позицию
        current_pos = self._file.tell()
        
        # Перемещаемся в начало файла
        self._file.seek(0)
        
        try:
            # Читаем данные
            data = self._file.read(size)
            return data
        finally:
            # Восстанавливаем позицию
            self._file.seek(current_pos)
        
    async def seek(self, offset: int) -> None:
        """Переместить указатель в файле"""
        self._file.seek(offset)
        
    async def close(self) -> None:
        """Закрыть файл"""
        self._file.close()
        
    async def save(self, path: str) -> None:
        """Сохранить файл на диск"""
        path = Path(path)
        
        # Создаем директорию, если она не существует
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
            
        # Сохраняем текущую позицию
        current_pos = self._file.tell()
        
        # Копируем файл
        self._file.seek(0)
        with open(path, "wb") as f:
            shutil.copyfileobj(self._file, f)
            
        # Восстанавливаем позицию
        self._file.seek(current_pos)
            
    async def __aiter__(self):
        """Итератор для чтения файла по частям"""
        # Сохраняем текущую позицию
        current_pos = self._file.tell()
        
        # Перемещаемся в начало файла
        self._file.seek(0)
        
        try:
            while True:
                chunk = self._file.read(self._chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            # Восстанавливаем позицию
            self._file.seek(current_pos)
        
    async def __aenter__(self) -> "UploadFile":
        """Контекстный менеджер для работы с файлом"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрыть файл при выходе из контекстного менеджера"""
        await self.close() 