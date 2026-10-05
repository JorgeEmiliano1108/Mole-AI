"""Local privacy utilities — breaks coupling with core_backend.

Usa HMAC-SHA256 con la clave compartida `ANONIMIZACION_KEY` para que los
identificadores pseudonimizados en MS1 sean coherentes con la tabla espejo
del backend (`training_dataset_anon`).
"""
import hashlib
import hmac
import os


def anonymize_id(value: str) -> str:
    """Retorna HMAC-SHA256 de un identificador para cumplimiento LFPDPPP."""
    if not value:
        return "anonymous"
    key = os.getenv("ANONIMIZACION_KEY", "").encode("utf-8")
    if not key:
        raise RuntimeError("ANONIMIZACION_KEY no configurada")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
