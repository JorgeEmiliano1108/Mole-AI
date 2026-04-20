"""
Sanitiza PII (Información Personal Identificable) en textos antes de enviarlos al LLM o logs.
"""
import re
import hashlib
from typing import Optional

class PIISanitizer:
    """Motor de sanitización de PII para cumplimiento normativo LFPDPPP."""
    
    # Patrones para correos y teléfonos (incluyendo ladas internacionales/MX)
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_PATTERN = re.compile(r'(\+?52)?\s?(\d{2,3}[\s-]?){3,4}\d')
    
    @classmethod
    def sanitize(cls, text: Optional[str]) -> str:
        """Detecta y enmascara correos y teléfonos en el texto crudo."""
        if not text:
            return ""
        
        # Reemplazo de coincidencias con etiquetas seguras (Data Masking)
        texto_limpio = cls.EMAIL_PATTERN.sub('[EMAIL_OCULTO]', text)
        texto_limpio = cls.PHONE_PATTERN.sub('[TEL_OCULTO]', texto_limpio)
        
        return texto_limpio
    
    @staticmethod
    def hash_user_id(user_id: Optional[str]) -> str:
        """Aplica hash SHA-256 irreversible a los identificadores para los logs."""
        if not user_id:
            return "anonymous"
        return hashlib.sha256(user_id.encode('utf-8')).hexdigest()