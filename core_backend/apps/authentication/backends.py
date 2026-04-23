# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Custom authentication backends for Mole.AI.

Supports dual login (username or email) as required by the architecture.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class DualLoginBackend(ModelBackend):
    """
    Backend de autenticación que permite login con username o email.
    Extiende ModelBackend para mantener toda la funcionalidad original.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Case-insensitive search en username y email
        try:
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Ejecutar hasher para prevenir timing attacks
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user):
        """Verificar que el usuario está activo y no está bloqueado."""
        is_active = getattr(user, "is_active", None)
        if is_active is False:
            return False
        return True