from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock


class VisionStatusViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _call(self, task_id):
        return self.client.get(f'/api/v1/ai/vision/status/{task_id}/')

    @patch('apps.ai_models.presentation.views.AsyncResult')
    def test_pending_returns_pending_status(self, mock_async):
        m = MagicMock()
        m.state = 'PENDING'
        m.info = None
        mock_async.return_value = m

        resp = self._call('task-pending')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'pending'

    @patch('apps.ai_models.presentation.views.AsyncResult')
    def test_success_returns_result_serializable(self, mock_async):
        m = MagicMock()
        m.state = 'SUCCESS'
        m.result = {'foo': 'bar'}
        mock_async.return_value = m

        resp = self._call('task-success')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'success'
        assert isinstance(data['result'], dict)

    @patch('apps.ai_models.presentation.views.AsyncResult')
    def test_success_handles_nonserializable_result(self, mock_async):
        class Bogus:
            def __str__(self):
                return 'bogus-object'

        m = MagicMock()
        m.state = 'SUCCESS'
        m.result = Bogus()
        mock_async.return_value = m

        resp = self._call('task-success-bogus')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'success'
        # result should be stringified fallback
        assert isinstance(data['result'], str) or data['result'] == 'bogus-object'

    @patch('apps.ai_models.presentation.views.AsyncResult')
    def test_failure_stringifies_info(self, mock_async):
        class MyErr(Exception):
            def __str__(self):
                return 'boom! details'

        m = MagicMock()
        m.state = 'FAILURE'
        m.info = MyErr('boom')
        mock_async.return_value = m

        resp = self._call('task-fail')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'failure'
        assert isinstance(data['error'], str)
