# -*- coding: utf-8 -*-
"""
Custom Django field for transparent encryption at rest.
Uses AES‑GCM‑256 (cryptography library) and a secret supplied via the
environment variable ``DJANGO_LTK_ENCRYPTION_KEY``.
The key must be a 32‑byte base64‑url‑safe string.
"""

import base64
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Retrieve the raw encryption key (32 bytes) from env var
_key_b64 = os.getenv("DJANGO_LTK_ENCRYPTION_KEY")
if not _key_b64:
    raise ImproperlyConfigured("DJANGO_LTK_ENCRYPTION_KEY environment variable is required for EncryptedCharField")
try:
    _encryption_key = base64.urlsafe_b64decode(_key_b64)
except Exception as exc:
    raise ImproperlyConfigured("DJANGO_LTK_ENCRYPTION_KEY must be base64‑url‑safe encoded") from exc
if len(_encryption_key) != 32:
    raise ImproperlyConfigured("DJANGO_LTK_ENCRYPTION_KEY must decode to 32 bytes (AES‑256 key)")


class EncryptedCharField(models.CharField):
    """CharField that encrypts data before storing it in the DB.
    The stored value is base64‑encoded ``nonce + ciphertext + tag``.
    """

    def __init__(self, *args, **kwargs):
        # Ensure max_length is sufficient for encrypted payload (nonce 12 + tag 16 + ciphertext)
        # We keep the original max_length for validation of plaintext length.
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """Encrypt the plaintext before DB insertion."""
        if value is None:
            return None
        # Ensure value is str
        if not isinstance(value, str):
            value = str(value)
        aesgcm = AESGCM(_encryption_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
        # Store nonce + ciphertext (ciphertext already contains tag at the end)
        encrypted = nonce + ciphertext
        return base64.urlsafe_b64encode(encrypted).decode("ascii")

    def from_db_value(self, value, expression, connection):
        """Decrypt the stored value when reading from DB."""
        if value is None:
            return None
        try:
            encrypted = base64.urlsafe_b64decode(value)
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            aesgcm = AESGCM(_encryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception:
            # If decryption fails, return raw value to avoid crashes – treat as corrupted data.
            return value

    def to_python(self, value):
        """Convert raw DB value to Python (called by Django field machinery)."""
        if isinstance(value, str):
            # When coming from DB, ``from_db_value`` already decrypted.
            return value
        return super().to_python(value)
