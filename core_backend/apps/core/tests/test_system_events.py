from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.core.models import AuditLog, Device


class SystemEventsTests(APITestCase):
    """GET /api/v1/admin/system-events/ — solo admin (issue N-0)."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='adm', password='x', is_staff=True)
        self.bot = User.objects.create_user(username='bot', password='x')

    def test_system_events_requires_authentication(self):
        resp = self.client.get('/api/v1/admin/system-events/')
        self.assertIn(resp.status_code, (401, 403))

    def test_system_events_forbidden_for_botanist(self):
        self.client.force_authenticate(user=self.bot)
        resp = self.client.get('/api/v1/admin/system-events/')
        self.assertEqual(resp.status_code, 403)

    def test_system_events_sections_for_admin(self):
        AuditLog.objects.create(user_id=self.bot.id, action="PASSWORD_RESET_REQUESTED",
                                details="Password reset solicitado.")
        _ = Device.objects.create(owner=self.admin, name='nodo-off',
                                  auth_token='tok-off', status='offline')

        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v1/admin/system-events/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for section in ('security', 'devices', 'telemetry', 'services'):
            self.assertIn(section, data)

        sec_actions = [e['action'] for e in data['security']]
        self.assertIn('PASSWORD_RESET_REQUESTED', sec_actions)
        # Sin PII: nunca IP.
        for e in data['security']:
            self.assertNotIn('ip_address', e)

        dev_ids = [e['device_id'] for e in data['devices']]
        self.assertTrue(any(dev_ids))
        self.assertTrue(all(e['tipo'] in ('warn', 'error') for e in data['devices']))

        for s in data['services']:
            self.assertIn('service', s)
            self.assertIn(s['status'], ('up', 'down'))
