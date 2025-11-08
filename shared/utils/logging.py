"""
Structured Logging for Cerberus
JSON-formatted logs for production observability
"""
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    
    Outputs logs in JSON format with consistent fields:
    - timestamp: ISO 8601 format
    - level: Log level
    - service: Service name
    - message: Log message
    - context: Additional context dict
    - error: Error details (if exception)
    """
    
    def __init__(self, service_name: str = "cerberus"):
        """
        Initialize JSON formatter
        
        Args:
            service_name: Name of the service (gatekeeper, sentinel, etc.)
        """
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        
        Args:
            record: Log record
            
        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra context from record
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add common fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        
        if hasattr(record, "event_id"):
            log_data["event_id"] = record.event_id
        
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        
        return json.dumps(log_data)


def setup_logging(
    service_name: str,
    level: str = "INFO",
    json_format: bool = True
) -> logging.Logger:
    """
    Setup structured logging for a Cerberus service
    
    Args:
        service_name: Name of service (gatekeeper, sentinel, etc.)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatter (default True for production)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        formatter = JSONFormatter(service_name)
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    Log message with additional context
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        context: Additional context dict
        **kwargs: Additional fields (request_id, session_id, etc.)
    """
    extra = {}
    
    if context:
        extra["context"] = context
    
    # Add kwargs as extra fields
    for key, value in kwargs.items():
        extra[key] = value
    
    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra)


class ContextLogger:
    """
    Logger with automatic context injection
    
    Useful for maintaining context across multiple log calls
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        default_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize context logger
        
        Args:
            logger: Base logger
            default_context: Context to include in all logs
        """
        self.logger = logger
        self.default_context = default_context or {}
    
    def _log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal log method with context merging"""
        merged_context = {**self.default_context, **(context or {})}
        log_with_context(self.logger, level, message, merged_context, **kwargs)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        self._log("debug", message, context, **kwargs)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        self._log("info", message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        self._log("warning", message, context, **kwargs)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        self._log("error", message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message"""
        self._log("critical", message, context, **kwargs)
    
    def with_context(self, **kwargs) -> "ContextLogger":
        """
        Create new context logger with additional context
        
        Args:
            **kwargs: Additional context fields
            
        Returns:
            New ContextLogger with merged context
        """
        merged_context = {**self.default_context, **kwargs}
        return ContextLogger(self.logger, merged_context)


# Example usage:
"""
# Setup logging
logger = setup_logging("gatekeeper", level="INFO", json_format=True)

# Simple logging
logger.info("Request received")

# Logging with context
log_with_context(
    logger,
    "info",
    "Request inspected",
    context={"action": "allow", "score": 0.25},
    request_id="req_123",
    session_id="sess_456"
)

# Using context logger
ctx_logger = ContextLogger(logger, {"service": "gatekeeper", "version": "1.0"})
ctx_logger.info("Starting inspection", request_id="req_789")

# Create child context
request_logger = ctx_logger.with_context(request_id="req_789", session_id="sess_456")
request_logger.info("ML analysis started")
request_logger.info("ML analysis complete", context={"score": 0.92})
"""
