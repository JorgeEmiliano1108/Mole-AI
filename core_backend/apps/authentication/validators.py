# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Custom serializer validators for Mole.AI authentication.
"""
import re
from rest_framework import serializers


class SecurePasswordValidator:
    """
    Validador de contraseña conforming a mejores prácticas NIST 2024.
    Regex: mínimo 6 caracteres, 1 mayúscula, 1 minúscula, 1 número.
    """

    PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$")
    ERROR_MESSAGE = (
        "La contraseña debe tener al menos 6 caracteres, "
        "incluir una mayúscula, una minúscula y un número."
    )

    def validate(self, password):
        if not self.PATTERN.match(password):
            raise serializers.ValidationError(self.ERROR_MESSAGE)
        return password


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Función helper para validar contraseña desde views.
    Retorna (is_valid, error_message).
    """
    if not SecurePasswordValidator.PATTERN.match(password):
        return False, SecurePasswordValidator.ERROR_MESSAGE
    return True, ""