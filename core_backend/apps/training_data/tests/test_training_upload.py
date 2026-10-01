from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase


def _payload(**kw):
    base = {'original_name': 'doc.pdf', 'content_type': 'application/pdf',
            'file_size': 1024}
    base.update(kw)
    return base


class TrainingUploadTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='tadm', password='x',
                                              is_staff=True)
        self.bot = User.objects.create_user(username='tbot', password='x')

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.bot)
        resp = self.client.post('/api/v1/training/documents/upload/request/',
                                _payload(), format='json')
        self.assertEqual(resp.status_code, 403)

    def test_oversize_rejected(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/v1/training/documents/upload/request/',
                                _payload(file_size=10**12), format='json')
        self.assertEqual(resp.status_code, 400)

    @override_settings(AWS_ACCESS_KEY_ID='test',
                         AWS_SECRET_ACCESS_KEY='test',
                         AWS_S3_ENDPOINT_URL='http://localhost:9000',
                         AWS_S3_REGION_NAME='us-east-1')
    def test_request_creates_pending_record(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/v1/training/documents/upload/request/',
                                _payload(), format='json')
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        for k in ('presigned_url', 's3_key', 'record_id', 'expires_in'):
            self.assertIn(k, body)
        from apps.training_data.models import TrainingDocument
        rec = TrainingDocument.objects.get(id=body['record_id'])
        self.assertEqual(rec.status, 'PENDING')
        self.assertEqual(rec.uploaded_by, self.admin)

    def test_list_documents_requires_auth(self):
        resp = self.client.get('/api/v1/training/documents/')
        self.assertIn(resp.status_code, (401, 403))

    def test_list_documents_requires_admin(self):
        self.client.force_authenticate(user=self.bot)
        resp = self.client.get('/api/v1/training/documents/')
        self.assertEqual(resp.status_code, 403)

    def test_list_documents_includes_record_id(self):
        from apps.training_data.models import TrainingDocument
        rec = TrainingDocument.objects.create(
            uploaded_by=self.admin,
            s3_key='k',
            s3_bucket='b',
            original_name='x.pdf',
            content_type='application/pdf',
            file_size=1,
            status='PENDING',
        )
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v1/training/documents/')
        self.assertEqual(resp.status_code, 200)
        item = resp.json()['results'][0]
        self.assertEqual(str(item['record_id']), str(rec.id))
