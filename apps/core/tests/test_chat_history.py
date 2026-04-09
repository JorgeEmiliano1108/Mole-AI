from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ai_models.models import LLMRequest


class ChatHistoryIsolationTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username='usera', password='pass')
        self.user_b = User.objects.create_user(username='userb', password='pass')

        # Create LLMRequest entries for user A
        LLMRequest.objects.create(
            user=self.user_a,
            session_id='sess-a-1',
            request_type='chat_conversation',
            prompt='hello A',
            model_name='mole-test',
            temperature=0.5,
            max_tokens=10,
            response='hi from A',
            processing_time_ms=10,
            status='completed'
        )

        self.client = APIClient()

    def test_user_b_gets_no_entries(self):
        # Authenticate as user B and fetch chat history
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get('/api/v1/chat/history/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'results' in data
        assert isinstance(data['results'], list)
        assert len(data['results']) == 0

    def test_user_a_gets_own_entries(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get('/api/v1/chat/history/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'results' in data
        assert len(data['results']) >= 1
