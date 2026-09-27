from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from jwt import InvalidSignatureError
from rest_framework import exceptions

from apps.authentication.infrastructure.authentication import (
    HardwareAPIKeyAuthentication,
    SupabaseAuthentication,
)


class SupabaseAuthenticationTests(TestCase):
    """Cobertura del fallback local HS256 y validaciones básicas (S4)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='local', email='local@finca.com', password='x')
        self.factory = RequestFactory()

    def _mint_local_jwt(self, sub=None, username=None, email=None, exp_minutes=10):
        now = datetime.now(timezone.utc)
        payload = {
            'sub': str(sub or self.user.id),
            'email': email or self.user.email,
            'exp': now + timedelta(minutes=exp_minutes),
            'iat': now,
            'jti': 'jti-1',
        }
        if username:
            payload['username'] = username
        return jwt.encode(
            payload,
            getattr(settings, 'JWT_SECRET_KEY', None) or settings.SECRET_KEY,
            algorithm='HS256',
        )

    def _request(self, token):
        return self.factory.post(
            '/api/v1/sensors/ingest',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

    def test_no_header_returns_none(self):
        auth = SupabaseAuthentication()
        self.assertIsNone(auth.authenticate(self.factory.get('/')))

    def test_malformed_bearer_raises(self):
        auth = SupabaseAuthentication()
        with self.assertRaises(exceptions.AuthenticationFailed):
            auth.authenticate(self.factory.get('/', HTTP_AUTHORIZATION='Bearer'))

    @patch('apps.authentication.jwks.get_verification_key')
    def test_local_hs256_by_username(self, mock_get_key):
        mock_get_key.side_effect = InvalidSignatureError('no jwks in test')
        token = self._mint_local_jwt(username=self.user.username)
        user, _ = SupabaseAuthentication().authenticate(self._request(token))
        self.assertEqual(user.id, self.user.id)

    @patch('apps.authentication.jwks.get_verification_key')
    def test_local_hs256_user_not_found(self, mock_get_key):
        mock_get_key.side_effect = InvalidSignatureError('no jwks in test')
        token = self._mint_local_jwt(username='nadie')
        with self.assertRaises(exceptions.AuthenticationFailed):
            SupabaseAuthentication().authenticate(self._request(token))

    @patch('apps.authentication.jwks.get_verification_key')
    def test_local_hs256_inactive_user(self, mock_get_key):
        mock_get_key.side_effect = InvalidSignatureError('no jwks in test')
        self.user.is_active = False
        self.user.save()
        token = self._mint_local_jwt(username=self.user.username)
        with self.assertRaises(exceptions.AuthenticationFailed):
            SupabaseAuthentication().authenticate(self._request(token))

    @patch('apps.authentication.jwks.get_verification_key')
    def test_local_hs256_superuser_path(self, mock_get_key):
        mock_get_key.side_effect = InvalidSignatureError('no jwks in test')
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        token = self._mint_local_jwt(username=self.user.username)
        user, _ = SupabaseAuthentication().authenticate(self._request(token))
        self.assertTrue(user.is_superuser)


class HardwareAPIKeyAuthenticationTests(TestCase):
    """Cobertura de la autenticación por clave global de hardware (S4)."""

    def setUp(self):
        self.factory = RequestFactory()
        self.auth = HardwareAPIKeyAuthentication()

    def test_no_key_returns_none(self):
        self.assertIsNone(
            self.auth.authenticate(self.factory.post('/api/v1/sensor-data/')))

    @patch.object(settings, 'HARDWARE_API_KEY', '')
    def test_unconfigured_raises(self):
        req = self.factory.post(
            '/api/v1/sensor-data/',
            HTTP_X_HARDWARE_API_KEY='abc')
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.auth.authenticate(req)

    def test_invalid_key_raises(self):
        req = self.factory.post(
            '/api/v1/sensor-data/',
            HTTP_X_HARDWARE_API_KEY='nope')
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.auth.authenticate(req)

    def test_valid_key_returns_hardware_user(self):
        req = self.factory.post(
            '/api/v1/sensor-data/',
            HTTP_X_HARDWARE_API_KEY=settings.HARDWARE_API_KEY)
        user, key = self.auth.authenticate(req)
        self.assertTrue(getattr(user, 'is_hardware_device', False))
        self.assertEqual(key, settings.HARDWARE_API_KEY)
        self.assertEqual(self.auth.authenticate_header(req), 'X-Hardware-Api-Key')
