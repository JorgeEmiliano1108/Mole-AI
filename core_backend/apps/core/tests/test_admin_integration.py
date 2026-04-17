from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class AdminIntegrationTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='normal', password='pass123')
        self.admin = User.objects.create_user(username='super', password='pass123', is_staff=True, is_superuser=True)
        self.client = APIClient()

    def test_admin_stats_requires_admin(self):
        url = '/api/v1/admin/stats/'

        # Unauthenticated should be rejected (401 or 403 depending on config)
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # Authenticated normal user -> Forbidden
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

        # Admin user -> OK and shape contains expected keys
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn('health', data)
        self.assertIn('users', data)
        self.assertIn('regs', data)

    def test_live_alerts_requires_admin(self):
        url = '/api/v1/admin/telemetry/latest/'

        # Unauthenticated
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # Normal user forbidden
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

        # Admin user gets JSON with alerts key
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn('alerts', data)
        self.assertIsInstance(data['alerts'], list)
