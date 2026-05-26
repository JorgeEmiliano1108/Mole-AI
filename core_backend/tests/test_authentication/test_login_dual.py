# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Tests para el sistema de autenticación dual (username o email).
Valida que el backend DualLoginBackend permite login con usuario o correo.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


class DualLoginTestCase(TestCase):
    """Test cases para autenticación dual (username o email)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="agricultor_test",
            email="test@mole.ai",
            password="Test1234"
        )

    def test_login_with_username(self):
        """Verificar que login con username funciona correctamente."""
        response = self.client.post(
            "/api/v1/auth/validate-token/",
            {"username": "agricultor_test", "password": "Test1234"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("token", data)
        self.assertEqual(data.get("role"), "user")

    def test_login_with_email(self):
        """Verificar que login con email funciona (Dual Login Backend)."""
        response = self.client.post(
            "/api/v1/auth/validate-token/",
            {"username": "test@mole.ai", "password": "Test1234"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("token", data)
        self.assertEqual(data.get("role"), "user")

    def test_login_case_insensitive_username(self):
        """Verificar que username es case-insensitive."""
        response = self.client.post(
            "/api/v1/auth/validate-token/",
            {"username": "AGRICULTOR_TEST", "password": "Test1234"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_case_insensitive_email(self):
        """Verificar que email es case-insensitive."""
        response = self.client.post(
            "/api/v1/auth/validate-token/",
            {"username": "TEST@MOLE.AI", "password": "Test1234"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid_credentials(self):
        """Verificar que credenciales inválidas devuelven 401."""
        response = self.client.post(
            "/api/v1/auth/validate-token/",
            {"username": "agricultor_test", "password": "WrongPass123"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Verificar que usuario inexistente devuelve 401."""
        response = self.client.post(
            "/api/v1/auth/validate-token/",
            {"username": "nobody@test.com", "password": "Test1234"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)