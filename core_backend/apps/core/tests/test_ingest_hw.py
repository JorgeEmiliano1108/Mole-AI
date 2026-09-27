from typing import ClassVar

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import Device, SensorLog
from apps.plants.models import UserPlant


class IngestHwTests(TestCase):
    """POST /api/v1/sensors/ingest — JWT + anti-replay (issue S4)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='hw', password='x')
        self.plant = UserPlant.objects.create(user=self.user, nickname='H')
        self.device = Device.objects.create(
            owner=self.user, name='d', auth_token='tok-hw-123')
        self.client = APIClient()
        resp = self.client.post('/api/v1/auth/login/',
                                {'username': 'hw', 'password': 'x'},
                                format='json')
        assert resp.status_code == 200, resp.content[:200]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {resp.json()['token']}")

    def _payload(self, **kw):
        base = {'plant_id': str(self.plant.id),
                'recorded_at': timezone.now().isoformat(),
                'soil_humidity': 42.0}
        base.update(kw)
        return base

    def test_anon_rejected(self):
        anon = APIClient()
        resp = anon.post('/api/v1/sensors/ingest', {},
                         content_type='application/json')
        self.assertIn(resp.status_code, (401, 403))

    def test_valid_ingest_201(self):
        resp = self.client.post(
            '/api/v1/sensors/ingest', data=self._payload(),
            format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(SensorLog.objects.filter(
            plant_id=self.plant.id).exists())

    def test_stale_timestamp_rejected(self):
        from datetime import timedelta
        old = (timezone.now() - timedelta(hours=2)).isoformat()
        resp = self.client.post(
            '/api/v1/sensors/ingest', data=self._payload(recorded_at=old),
            format='json')
        self.assertIn(resp.status_code, (400, 403))

    def test_unknown_plant_404(self):
        import uuid
        resp = self.client.post(
            '/api/v1/sensors/ingest',
            data=self._payload(plant_id=str(uuid.uuid4())),
            format='json')
        self.assertEqual(resp.status_code, 404)

    def test_empty_payload_400(self):
        resp = self.client.post(
            '/api/v1/sensors/ingest',
            data={'plant_id': str(self.plant.id)},
            format='json')
        self.assertEqual(resp.status_code, 400)


class EdgeBatchTests(TestCase):
    def test_device_bearer_permission(self):
        from django.contrib.auth import get_user_model

        from apps.core.models import Device
        from apps.core.views import DeviceBearerPermission
        User = get_user_model()
        u = User.objects.create_user(username='eb', password='x')
        Device.objects.create(owner=u, name='d', auth_token='tok-eb')
        perm = DeviceBearerPermission()

        class Req:
            headers: ClassVar[dict] = {'Authorization': 'Bearer tok-eb'}
        self.assertTrue(perm.has_permission(Req(), None))

        class Bad:
            headers: ClassVar[dict] = {'Authorization': 'Bearer nope'}
        from rest_framework import exceptions
        with self.assertRaises(exceptions.AuthenticationFailed):
            perm.has_permission(Bad(), None)
