from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.core.models import AuditLog, Device


class AdminPortalTests(APITestCase):
    """GET admin/audit-log + admin/devices/ — solo admin (issue N-2)."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='adm2', password='x', is_staff=True)
        self.bot = User.objects.create_user(username='bot2', password='x')

    def test_audit_log_forbidden_for_botanist(self):
        self.client.force_authenticate(user=self.bot)
        for url in ('/api/v1/admin/audit-log/', '/api/v1/admin/devices/'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403, url)

    def test_audit_log_lists_and_filters(self):
        AuditLog.objects.create(user_id=self.bot.id, action="ADMIN_UPDATE_USER",
                                details="Actualizado user_id=1.")
        AuditLog.objects.create(user_id=self.bot.id, action="PASSWORD_CHANGED",
                                details="Password cambiado.")
        self.client.force_authenticate(user=self.admin)

        resp = self.client.get('/api/v1/admin/audit-log/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 2)
        self.assertIn('ip_address', data['results'][0])

        resp = self.client.get('/api/v1/admin/audit-log/?action=ADMIN')
        self.assertEqual(resp.json()['count'], 1)
        self.assertEqual(resp.json()['results'][0]['action'], 'ADMIN_UPDATE_USER')

    def test_admin_devices_no_tokens(self):
        Device.objects.create(owner=self.bot, name='nodo-x', auth_token='sekret',
                              status='warning')
        self.client.force_authenticate(user=self.admin)

        resp = self.client.get('/api/v1/admin/devices/')
        self.assertEqual(resp.status_code, 200)
        rows = resp.json()['results']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'nodo-x')
        self.assertEqual(rows[0]['status'], 'warning')
        self.assertEqual(rows[0]['owner'], 'bot2')
        # El Bearer jamás sale por API.
        self.assertNotIn('auth_token', rows[0])
        self.assertNotIn('sekret', str(rows[0]))
