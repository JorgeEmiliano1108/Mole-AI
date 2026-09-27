from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AiModelsViewsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='aim', password='x')
        self.client.force_authenticate(user=self.user)

    def test_monitoring_placeholders(self):
        for url in ('/api/v1/ai/llm/requests/', '/api/v1/ai/cnn/inferences/',
                    '/api/v1/ai/performance/', '/api/v1/ai/config/',
                    '/api/v1/ai/health/'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)

    def test_anon_rejected(self):
        from rest_framework.test import APIClient
        anon = APIClient()
        self.assertIn(anon.get('/api/v1/ai/health/').status_code, (401, 403))
