from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.core.models import AmbientReading, Device, SoilReading
from apps.plants.models import UserPlant


class LiveAlertsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='la', password='x',
                                              is_staff=True)
        self.client.force_authenticate(user=self.admin)

    def test_stable_when_empty(self):
        resp = self.client.get('/api/v1/admin/live-alerts/')
        self.assertEqual(resp.status_code, 200)
        alerts = resp.json()['alerts']
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['tipo'], 'info')

    def test_thresholds_and_cap(self):
        User = get_user_model()
        u = User.objects.create_user(username='la2', password='x')
        p = UserPlant.objects.create(user=u, nickname='P')
        d = Device.objects.create(owner=u, name='d', auth_token='tok-la')
        from apps.core.models import HardwareBinding
        b = HardwareBinding.objects.create(device=d, hardware_pin='32', plant=p)
        SoilReading.objects.create(binding=b, soil_humidity=10.0)
        AmbientReading.objects.create(device=d, uv_index=12.0,
                                      air_temperature=31.0)
        resp = self.client.get('/api/v1/admin/live-alerts/')
        self.assertEqual(resp.status_code, 200)
        alerts = resp.json()['alerts']
        self.assertLessEqual(len(alerts), 5)
        tipos = {a['tipo'] for a in alerts}
        self.assertIn('error', tipos)
        self.assertIn('warn', tipos)

    def test_botanist_forbidden(self):
        User = get_user_model()
        bot = User.objects.create_user(username='lab', password='x')
        self.client.force_authenticate(user=bot)
        self.assertEqual(
            self.client.get('/api/v1/admin/live-alerts/').status_code, 403)


class MasterReportTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='mr', password='x',
                                              is_staff=True)
        self.client.force_authenticate(user=self.admin)

    def test_generate_ok(self):
        fake = MagicMock(status_code=200)
        fake.json.return_value = {'job_id': 'j1'}
        with patch('apps.core.admin_views.requests.post', return_value=fake):
            resp = self.client.post('/api/v1/admin/reports/generate/', {},
                                    format='json')
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.json()['job_id'], 'j1')

    def test_generate_ms_down(self):
        with patch('apps.core.admin_views.requests.post',
                   side_effect=ConnectionError('down')):
            resp = self.client.post('/api/v1/admin/reports/generate/', {},
                                    format='json')
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.json()['status'], 'failed')

    def test_status_success_with_download(self):
        st = MagicMock(status_code=200)
        st.json.return_value = {'status': 'SUCCESS'}
        dl = MagicMock(status_code=200)
        dl.json.return_value = {'download_url': 'http://f/x.pdf'}
        with patch('apps.core.admin_views.requests.get', side_effect=[st, dl]):
            resp = self.client.get('/api/v1/admin/reports/j1/status/')
        self.assertEqual(resp.json()['status'], 'completed')
        self.assertIn('x.pdf', resp.json()['file_url'])

    def test_status_failed(self):
        st = MagicMock(status_code=200)
        st.json.return_value = {'status': 'FAILED'}
        with patch('apps.core.admin_views.requests.get', return_value=st):
            resp = self.client.get('/api/v1/admin/reports/j1/status/')
        self.assertEqual(resp.json()['status'], 'failed')


class PdfDownloadTests(TestCase):
    def test_download_pdf(self):
        import uuid

        from apps.core.models import AIDiagnostic
        User = get_user_model()
        u = User.objects.create_user(username='pdfd', password='x')
        d = AIDiagnostic.objects.create(user=u, plant_id=uuid.uuid4(),
                                        diagnosis_label='Roya')
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(user=u)
        resp = c.get(f'/api/v1/diagnostics/{d.id}/download/')
        self.assertEqual(resp.status_code, 202)
        body = resp.json()
        self.assertEqual(body['status'], 'processing')
        self.assertIn('task_id', body)
