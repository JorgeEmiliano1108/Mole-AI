"""
Sanitiza PII (Información Personal Identificable) en textos antes de enviarlos al LLM o logs.
"""
import re
import hashlib
import logging
from typing import Optional

class PIISanitizer:
    """Motor de sanitización de PII para cumplimiento normativo LFPDPPP."""
    
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_PATTERN = re.compile(r'(\+?52)?\s?(\d{2,3}[\s-]?){3,4}\d')
    
    @classmethod
    def sanitize(cls, text: Optional[str]) -> str:
        if not text:
            return ""
        texto_limpio = cls.EMAIL_PATTERN.sub('[EMAIL_OCULTO]', text)
        texto_limpio = cls.PHONE_PATTERN.sub('[TEL_OCULTO]', texto_limpio)
        return texto_limpio
    
    @staticmethod
    def hash_user_id(user_id: Optional[str]) -> str:
        if not user_id:
            return "anonymous"
        return hashlib.sha256(user_id.encode('utf-8')).hexdigest()


class PIILogFilter(logging.Filter):
    """Log filter that redacts PII from log messages and hashes user IDs.

    LFPDPPP compliance: email/phone patterns are masked,
    and any extra 'user_id' field is replaced with its SHA-256 hash.
    """
    def __init__(self, name: str = ""):
        super().__init__(name)

    def filter(self, record: logging.LogRecord) -> bool:
        # Sanitize the log message itself
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = PIISanitizer.sanitize(record.msg)
        # Sanitize positional args (common in structured logging)
        if record.args:
            sanitized_args = tuple(
                PIISanitizer.sanitize(str(a)) if isinstance(a, str) else a
                for a in record.args
            )
            record.args = sanitized_args
        # Hash any 'user_id' in extra
        if hasattr(record, 'user_id') and record.user_id:
            record.user_id = PIISanitizer.hash_user_id(record.user_id)
            # Also set as extra so structlog can pick it
            record.__dict__['user_hash'] = record.user_id
            del record.user_id
        return True