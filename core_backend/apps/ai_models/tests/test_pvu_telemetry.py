import uuid

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.ai_models.models import PvuRouteLog


class PvuTelemetryTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='pvu', password='x')
        self.client.force_authenticate(user=self.user)

    def test_log_pvu_route_requires_auth(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post('/api/v1/ai/pvu/route/', {}, format='json')
        self.assertIn(resp.status_code, (401, 403))

    def test_log_pvu_route_creates_record(self):
        resp = self.client.post('/api/v1/ai/pvu/route/', {
            'route': 'local',
            'reason': 'offline',
            'net': 'offline',
            'battery_pct': 0.5,
            'wifi_rssi': -85,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['status'], 'logged')
        log = PvuRouteLog.objects.get(user=self.user)
        self.assertEqual(log.route, 'local')
        self.assertEqual(log.reason, 'offline')
        self.assertEqual(log.net, 'offline')
        self.assertEqual(log.battery_pct, 0.5)
        self.assertEqual(log.wifi_rssi, -85)

    def test_log_pvu_route_truncates_long_fields(self):
        self.client.post('/api/v1/ai/pvu/route/', {
            'route': 'local' * 5,
            'reason': 'offline' * 10,
            'net': 'offline' * 5,
        }, format='json')
        log = PvuRouteLog.objects.get(user=self.user)
        self.assertEqual(len(log.route), 10)
        self.assertEqual(len(log.reason), 30)
        self.assertEqual(len(log.net), 10)


class DiagnosticPvuReasonTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='patch', password='x')
        self.client.force_authenticate(user=self.user)
        from apps.core.models import AIDiagnostic
        self.diag = AIDiagnostic.objects.create(
            user=self.user, plant_id=uuid.uuid4(), diagnosis_label='Mildiu')

    def test_patch_pvu_reason(self):
        resp = self.client.patch(
            f'/api/v1/diagnostics/{self.diag.id}/',
            {'pvu_reason': 'offline'},
            format='json')
        self.assertEqual(resp.status_code, 200)
        self.diag.refresh_from_db()
        self.assertEqual(self.diag.pvu_reason, 'offline')

    def test_patch_pvu_reason_missing(self):
        resp = self.client.patch(
            f'/api/v1/diagnostics/{self.diag.id}/',
            {},
            format='json')
        self.assertEqual(resp.status_code, 400)

    def test_patch_pvu_reason_not_owner_404(self):
        User = get_user_model()
        other = User.objects.create_user(username='other', password='x')
        self.client.force_authenticate(user=other)
        resp = self.client.patch(
            f'/api/v1/diagnostics/{self.diag.id}/',
            {'pvu_reason': 'offline'},
            format='json')
        self.assertEqual(resp.status_code, 404)
