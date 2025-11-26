"""
Logging system for QakeAPI.

Provides centralized logging functionality with configurable levels,
formatters, and handlers.
"""

import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json as json_module


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json_module.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logs."""
    
    def __init__(self, include_timestamp: bool = True):
        """
        Initialize text formatter.
        
        Args:
            include_timestamp: Whether to include timestamp in log messages
        """
        if include_timestamp:
            fmt = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
        else:
            fmt = "%(levelname)-8s %(name)s: %(message)s"
            datefmt = None
        
        super().__init__(fmt=fmt, datefmt=datefmt)


class QakeAPILogger:
    """
    Centralized logger for QakeAPI.
    
    Provides structured logging with configurable format and levels.
    """
    
    def __init__(
        self,
        name: str = "qakeapi",
        level: str = "INFO",
        format_type: str = "text",
        include_timestamp: bool = True,
    ):
        """
        Initialize QakeAPI logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_type: Format type ("text" or "json")
            include_timestamp: Whether to include timestamp (for text format)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.logger.propagate = False  # Prevent duplicate logs
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Set formatter
        if format_type == "json":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter(include_timestamp=include_timestamp)
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self._handlers: list = [console_handler]
    
    def add_file_handler(
        self,
        filepath: str,
        level: Optional[str] = None,
        format_type: str = "text",
    ) -> None:
        """
        Add file handler to logger.
        
        Args:
            filepath: Path to log file
            level: Logging level for file handler (default: same as logger)
            format_type: Format type ("text" or "json")
        """
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            filepath,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        
        if level:
            file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        else:
            file_handler.setLevel(self.logger.level)
        
        # Set formatter
        if format_type == "json":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter(include_timestamp=True)
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self._handlers.append(file_handler)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)
    
    def set_level(self, level: str) -> None:
        """Set logging level."""
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        for handler in self._handlers:
            handler.setLevel(getattr(logging, level.upper(), logging.INFO))


# Global logger instance
_logger: Optional[QakeAPILogger] = None


def get_logger(
    name: str = "qakeapi",
    level: str = "INFO",
    format_type: str = "text",
) -> QakeAPILogger:
    """
    Get or create global logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        format_type: Format type ("text" or "json")
        
    Returns:
        QakeAPILogger instance
    """
    global _logger
    
    if _logger is None:
        _logger = QakeAPILogger(name=name, level=level, format_type=format_type)
    
    return _logger


def configure_logging(
    level: str = "INFO",
    format_type: str = "text",
    filepath: Optional[str] = None,
    file_level: Optional[str] = None,
) -> QakeAPILogger:
    """
    Configure global logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ("text" or "json")
        filepath: Optional path to log file
        file_level: Optional logging level for file handler
        
    Returns:
        Configured QakeAPILogger instance
        
    Example:
        ```python
        from qakeapi.core.logging import configure_logging
        
        logger = configure_logging(
            level="DEBUG",
            format_type="json",
            filepath="app.log"
        )
        ```
    """
    global _logger
    
    _logger = QakeAPILogger(
        name="qakeapi",
        level=level,
        format_type=format_type,
    )
    
    if filepath:
        _logger.add_file_handler(filepath, level=file_level, format_type=format_type)
    
    return _logger

