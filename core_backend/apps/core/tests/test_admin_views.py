from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AdminViewsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='avt', password='x',
                                              is_staff=True)
        self.super = User.objects.create_superuser(username='sup', password='x',
                                                   email='s@x.io')
        self.bot = User.objects.create_user(username='bvt', password='x')
        self.client.force_authenticate(user=self.admin)

    def test_statistics_shape(self):
        resp = self.client.get('/api/v1/admin/statistics/')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for k in ('users', 'regs', 'health', 'total_plants'):
            self.assertIn(k, body)
        self.assertEqual(len(body['regs']), 7)
        self.assertEqual(len(body['health']), 5)

    def test_statistics_forbidden_botanist(self):
        self.client.force_authenticate(user=self.bot)
        self.assertEqual(
            self.client.get('/api/v1/admin/statistics/').status_code, 403)

    def test_users_crud(self):
        # create
        resp = self.client.post('/api/v1/admin/users/create/',
                                {'username': 'nuevo', 'password': 'Segura123!',
                                 'role': 'Operador'}, format='json')
        self.assertIn(resp.status_code, (200, 201))
        User = get_user_model()
        uid = User.objects.get(username='nuevo').id
        # list + filter
        resp = self.client.get('/api/v1/admin/users/?search=nuevo')
        self.assertEqual(resp.status_code, 200)
        # detail GET
        resp = self.client.get(f'/api/v1/admin/users/{uid}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['role'], 'Operador')
        # patch role
        resp = self.client.patch(f'/api/v1/admin/users/{uid}/',
                                 {'role': 'Admin'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['role'], 'Admin')
        # deactivate (soft)
        resp = self.client.delete(f'/api/v1/admin/users/{uid}/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.get(id=uid).is_active)

    def test_superadmin_guard(self):
        # Admin (no superuser) no puede tocar superadmin.
        resp = self.client.patch(
            f'/api/v1/admin/users/{self.super.id}/', {'role': 'Admin'},
            format='json')
        self.assertEqual(resp.status_code, 403)
        self.client.force_authenticate(user=self.super)
        resp = self.client.patch(
            f'/api/v1/admin/users/{self.bot.id}/', {'role': 'Admin'},
            format='json')
        self.assertEqual(resp.status_code, 200)

    def test_report_text(self):
        resp = self.client.get('/api/v1/admin/report-text/')
        self.assertEqual(resp.status_code, 200)
