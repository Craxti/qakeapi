"""
Tests for logging system.
"""

import pytest
import logging
from qakeapi.core.logging import (
    QakeAPILogger,
    JSONFormatter,
    TextFormatter,
    get_logger,
    configure_logging
)


class TestJSONFormatter:
    """Tests for JSONFormatter."""
    
    def test_json_formatter_format(self):
        """Test JSON formatter formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        assert "timestamp" in result
        assert "level" in result
        assert "message" in result
        assert "Test message" in result
    
    def test_json_formatter_with_exception(self):
        """Test JSON formatter with exception info."""
        import sys
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            result = formatter.format(record)
            assert "exception" in result


class TestTextFormatter:
    """Tests for TextFormatter."""
    
    def test_text_formatter_with_timestamp(self):
        """Test text formatter with timestamp."""
        formatter = TextFormatter(include_timestamp=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        assert "INFO" in result
        assert "test" in result
        assert "Test message" in result
    
    def test_text_formatter_without_timestamp(self):
        """Test text formatter without timestamp."""
        formatter = TextFormatter(include_timestamp=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result


class TestQakeAPILogger:
    """Tests for QakeAPILogger."""
    
    def test_logger_creation_text(self):
        """Test creating logger with text format."""
        logger = QakeAPILogger(name="test", level="INFO", format_type="text")
        assert logger.logger.name == "test"
        assert logger.logger.level == logging.INFO
    
    def test_logger_creation_json(self):
        """Test creating logger with JSON format."""
        logger = QakeAPILogger(name="test", level="DEBUG", format_type="json")
        assert logger.logger.name == "test"
        assert logger.logger.level == logging.DEBUG
    
    def test_logger_logging(self):
        """Test logger logging methods."""
        logger = QakeAPILogger(name="test", level="DEBUG")
        
        # Test different log levels
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.debug("Debug message")
        
        # Should not raise exceptions
        assert True


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_default(self):
        """Test getting default logger."""
        logger = get_logger()
        # get_logger returns QakeAPILogger instance, not logging.Logger
        assert hasattr(logger, "logger")
        assert isinstance(logger.logger, logging.Logger)
    
    def test_get_logger_with_name(self):
        """Test getting logger with name."""
        # get_logger doesn't accept name parameter, always returns global logger
        logger = get_logger()
        assert hasattr(logger, "logger")
        # Global logger has default name "qakeapi"
        assert logger.logger.name == "qakeapi"


class TestConfigureLogging:
    """Tests for configure_logging function."""
    
    def test_configure_logging_text(self):
        """Test configuring logging with text format."""
        logger = configure_logging(
            level="INFO",
            format_type="text"
        )
        assert hasattr(logger, "logger")
        assert isinstance(logger.logger, logging.Logger)
    
    def test_configure_logging_json(self):
        """Test configuring logging with JSON format."""
        logger = configure_logging(
            level="DEBUG",
            format_type="json"
        )
        assert hasattr(logger, "logger")
        assert isinstance(logger.logger, logging.Logger)

