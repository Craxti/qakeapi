"""
Модуль логирования для QakeAPI.
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
import sys

class JsonFormatter(logging.Formatter):
    """Форматтер для логов в JSON формате."""
    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи лога в JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Настройка логирования.
    
    Args:
        level: Уровень логирования
        json_output: Использовать JSON формат
        log_file: Путь к файлу логов
    """
    logger = logging.getLogger('qakeapi')
    logger.setLevel(level.upper())
    
    # Очищаем существующие обработчики
    logger.handlers = []
    
    # Создаем форматтер
    formatter = JsonFormatter() if json_output else logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Добавляем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Добавляем обработчик для файла, если указан
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

class RequestLogger:
    """Логгер для HTTP запросов."""
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def log_request(
        self,
        method: str,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        body: Any = None
    ) -> None:
        """Логирование входящего запроса."""
        self.logger.info(
            'Incoming request',
            extra={
                'method': method,
                'path': path,
                'params': params,
                'headers': headers,
                'body': body
            }
        )
        
    def log_response(
        self,
        status_code: int,
        body: Any = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """Логирование ответа."""
        self.logger.info(
            'Outgoing response',
            extra={
                'status_code': status_code,
                'body': body,
                'duration_ms': duration_ms
            }
        )

class StructuredLogger:
    """Logger with structured logging capabilities."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _log(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log message with extra fields."""
        self.logger.log(
            level,
            message,
            extra={"extra_fields": extra} if extra else None
        )
        
    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log info message."""
        self._log(logging.INFO, message, extra)
        
    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log error message."""
        if error:
            if not extra:
                extra = {}
            extra["error"] = {
                "type": type(error).__name__,
                "message": str(error)
            }
        self._log(logging.ERROR, message, extra)
        
    def warning(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log warning message."""
        self._log(logging.WARNING, message, extra)
        
    def debug(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log debug message."""
        self._log(logging.DEBUG, message, extra)

# Example usage:
"""
# Setup logging
logger = setup_logging(
    level="DEBUG",
    json_output=True,
    log_file="logs/app.log"
)

# Create structured logger
log = StructuredLogger("myapp")

# Log messages
log.info(
    "User logged in",
    extra={
        "user_id": "123",
        "ip_address": "127.0.0.1"
    }
)

log.error(
    "Database connection failed",
    error=db_error,
    extra={
        "database": "users",
        "retry_count": 3
    }
)

# Log requests
request_logger = RequestLogger(logger)
request_logger.log_request(
    method="POST",
    path="/api/users",
    status_code=201,
    duration=0.123,
    extra={
        "user_id": "123",
        "content_length": 1024
    }
)
""" 