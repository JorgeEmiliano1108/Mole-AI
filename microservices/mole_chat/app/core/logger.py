"""
Core Logging - structlog configuration
LFPDPPP compliance: PII is automatically hashed/masked in logs.
"""
import logging
import json

from app.core.pii_sanitizer import PIILogFilter


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extra = {}
        for key, value in record.__dict__.items():
            if key not in ('args', 'asctime', 'created', 'exc_info',
                           'exc_text', 'filename', 'funcName', 'levelname',
                           'levelno', 'lineno', 'module', 'msecs',
                           'message', 'msg', 'name', 'pathname',
                           'process', 'processName', 'relativeCreated',
                           'stack_info', 'thread', 'threadName'):
                extra[key] = value
        payload = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if extra:
            payload["extra"] = extra
        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON formatter and PII filter."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    handler.addFilter(PIILogFilter())
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(level)
    root.addHandler(handler)

logger = logging.getLogger("mole_chat")