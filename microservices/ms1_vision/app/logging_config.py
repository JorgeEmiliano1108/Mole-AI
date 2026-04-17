import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Extraer e inyectar el rastro de la excepción (Traceback) si existe
        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
            
        # include structured fields if provided
        for k, v in getattr(record, "extra_fields", {}).items():
            payload[k] = v
            
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(level)
    root.addHandler(handler)