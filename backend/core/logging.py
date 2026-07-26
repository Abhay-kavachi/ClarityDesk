"""
Structured JSON logging and context management for ClarityDesk.
Provides request correlation IDs (X-Request-ID) for operational traceability.
"""
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable to hold the correlation/request ID across async tasks
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class StructuredJsonFormatter(logging.Formatter):
    """
    Formats log records as structured JSON including timestamp, level,
    logger name, message, and request_id if available.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        req_id = request_id_ctx.get()
        if req_id:
            log_entry["request_id"] = req_id
            
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures root logger with JSON formatting."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    
    root_logger = logging.getLogger("claritydesk")
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    return root_logger
