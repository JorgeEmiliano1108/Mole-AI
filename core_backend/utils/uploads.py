"""Helpers compartidos de subida de archivos (Guardrail B, NOM-019).

Única fuente de verdad para persistir uploads de usuario sin path traversal:
todos los módulos que guarden archivos con nombres provistos por el cliente
(`diagnostic_view`, `analyze_vision_view`, `train_*_view`) deben usar
:func:`safe_temp_path` — prohibido `os.path.join` / f-strings con el nombre
original (ver `AGENTS.md`, skill `enforce-compliance`).
"""

import logging
import os
import tempfile
import uuid

from django.utils._os import safe_join

logger = logging.getLogger(__name__)


def safe_temp_path(filename, *, prefix="", base_dir=None):
    """Construye una ruta temporal segura para un upload.

    - ``base_dir``: directorio base (default: `tempfile.gettempdir()`).
    - ``filename``: nombre original del cliente; se reduce a basename
      (neutraliza `../../x` y rutas absolutas) y se prefija con uuid4,
      por lo que colisiones y traversal son imposibles.
    - Retorna str listo para `open(..., 'wb+')`. Crea `base_dir` si falta.
    """
    if base_dir is None:
        base_dir = tempfile.gettempdir()
    os.makedirs(base_dir, exist_ok=True)
    safe_name = f"{prefix}{uuid.uuid4().hex}_{os.path.basename(filename or 'upload.bin')}"
    return safe_join(base_dir, safe_name)


def assert_magic_image(file_obj):
    """Valida magic-bytes de imagen (jpeg/png/webp) + rechaza ejecutables.

    Mismo criterio que `DiagnosticRequestSerializer.validate_image`
    (contrato §5): `FFD8FF` / `89PNG` / `RIFF....WEBP`, anti `MZ`/`ELF`.
    Retorna None si ok; lanza `ValueError` con mensaje seguro para UI si no.
    No consume el stream (hace `seek(0)`).
    """
    header = file_obj.read(2048)
    try:
        file_obj.seek(0)
    except (OSError, AttributeError, ValueError):
        # Stream no rebobinable: se valida con el header ya leído.
        logger.debug("Upload no rebobinable; validando header parcial.")
    is_jpeg = header.startswith(b'\xff\xd8\xff')
    is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
    is_webp = header.startswith(b'RIFF') and header[8:12] == b'WEBP'
    if not (is_jpeg or is_png or is_webp):
        raise ValueError("Firma de archivo inválida. Posible binario camuflado.")
    if b'MZ' in header[:2] or b'\x7fELF' in header[:4]:
        raise ValueError("Ejecutable malicioso detectado.")
