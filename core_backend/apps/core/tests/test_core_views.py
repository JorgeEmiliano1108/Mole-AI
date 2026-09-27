from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.core.models import AIDiagnostic, FeedbackTicket


class CoreViewsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='cv', password='x')
        self.client.force_authenticate(user=self.user)

    def test_diagnostic_history_empty_and_filled(self):
        resp = self.client.get('/api/v1/diagnostics/history/')
        self.assertEqual(resp.json()['results'], [])
        import uuid
        AIDiagnostic.objects.create(user=self.user, plant_id=uuid.uuid4(),
                                    diagnosis_label='Mildiu')
        resp = self.client.get('/api/v1/diagnostics/history/?limit=20')
        self.assertEqual(len(resp.json()['results']), 1)
        self.assertEqual(resp.json()['results'][0]['condition'], 'Mildiu')

    def test_feedback_create_and_validate(self):
        resp = self.client.post('/api/v1/feedback/', {}, format='json')
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(
            '/api/v1/feedback/',
            {'topic': 'bug', 'message': 'Se cayó el nodo al regar x.'},
            format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(FeedbackTicket.objects.filter(
            user=self.user, topic='bug').exists())

    def test_placeholders(self):
        for url in ('/api/v1/history/', '/api/v1/plant-knowledge/'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)

    def test_sensor_log_stub(self):
        resp = self.client.post('/api/v1/reports/plants', {}, format='json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get('/api/v1/reports/plants')
        self.assertEqual(resp.status_code, 405)
