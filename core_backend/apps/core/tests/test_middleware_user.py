from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase
from rest_framework.test import APITestCase

from apps.authentication.middleware import get_user


def _jwt(uid, role='user'):
    import uuid
    from datetime import datetime, timedelta, timezone

    import jwt as pyjwt
    from django.conf import settings
    key = getattr(settings, 'JWT_SECRET_KEY', None) or settings.SECRET_KEY
    now = datetime.now(timezone.utc)
    return pyjwt.encode(
        {'sub': str(uid), 'role': role, 'aud': 'authenticated',
         'exp': now + timedelta(minutes=20), 'iat': now,
         'jti': uuid.uuid4().hex},
        key, algorithm='HS256')


class MiddlewareUserTests(TransactionTestCase):
    def test_get_user_minimal_jwt(self):
        User = get_user_model()
        u = User.objects.create_user(username='mw', password='x')
        user = async_to_sync(get_user)(_jwt(u.id))
        self.assertEqual(user, u)

    def test_get_user_garbage_anonymous(self):
        self.assertIsInstance(async_to_sync(get_user)('basura'), AnonymousUser)
        self.assertIsInstance(async_to_sync(get_user)(''), AnonymousUser)


class SpeciesRbacTests(APITestCase):
    def test_write_requires_staff(self):
        User = get_user_model()
        bot = User.objects.create_user(username='spb', password='x')
        self.client.force_authenticate(user=bot)
        resp = self.client.post('/api/v1/plants/species/',
                                {'scientific_name': 'X y',
                                 'common_name': 'X'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

    def test_read_open(self):
        resp = self.client.get('/api/v1/plants/species/')
        self.assertEqual(resp.status_code, 200)

    def test_mock_sensor_shape(self):
        resp = self.client.get('/api/v1/sensor-data/latest/')
        self.assertEqual(resp.status_code, 200)
        for k in ('temperature', 'humidity'):
            self.assertIn(k, resp.json())
