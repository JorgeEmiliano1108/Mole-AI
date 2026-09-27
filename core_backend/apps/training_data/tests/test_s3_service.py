from apps.training_data.services import S3TrainingService
from django.test import TestCase, override_settings


@override_settings(AWS_ACCESS_KEY_ID='test', AWS_SECRET_ACCESS_KEY='test',
                   AWS_S3_ENDPOINT_URL='http://localhost:9000',
                   AWS_S3_REGION_NAME='us-east-1')
class S3ServiceTests(TestCase):
    def test_document_key_sanitizes(self):
        k = S3TrainingService.generate_document_key('../../evil.pdf')
        self.assertTrue(k.startswith('documents/'))
        self.assertNotIn('..', k)
        self.assertTrue(k.endswith('.pdf'))

    def test_presigned_put_shape(self):
        svc = S3TrainingService()
        url = svc.generate_presigned_put_url(
            s3_key='documents/a.pdf', content_type='application/pdf',
            max_content_length=1024, ttl=900)
        self.assertIn('http', url)
