from apps.training_data.models import TrainingDocument
from apps.training_data.tasks import notify_training_asset, update_training_status
from django.contrib.auth import get_user_model
from django.test import TestCase


class TrainingTasksTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='tt', password='x',
                                              is_staff=True)
        self.doc = TrainingDocument.objects.create(
            uploaded_by=self.admin, s3_key='documents/t.pdf',
            original_name='t.pdf', content_type='application/pdf',
            file_size=10, status='PENDING')

    def test_notify_publishes_without_pii(self):
        out = notify_training_asset(str(self.doc.id), 'document')
        self.assertEqual(out['status'], 'notified')
        self.assertEqual(out['channel'], 'mole:training:new_asset')
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, 'INDEXING')

    def test_notify_unknown_asset_raises(self):
        with self.assertRaises(Exception):
            notify_training_asset(str(self.doc.id), 'nave')

    def test_status_lifecycle(self):
        out = update_training_status(str(self.doc.id), 'document', 'INDEXED')
        self.assertEqual(out['new_status'], 'INDEXED')
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, 'INDEXED')
        self.assertIsNotNone(self.doc.processed_at)

    def test_status_invalid_rejected(self):
        with self.assertRaises(Exception):
            update_training_status(str(self.doc.id), 'document', 'NOPE')
