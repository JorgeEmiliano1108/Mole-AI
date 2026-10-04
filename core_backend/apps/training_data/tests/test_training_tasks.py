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


class PurgeOldRagChunksTests(TestCase):
    def _ensure_table(self):
        from django.db import connection
        with connection.cursor() as cursor:
            # DDL portable para sqlite (la task solo filtra por created_at).
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS rag_knowledge_chunks ("
                "id TEXT PRIMARY KEY, doc_id TEXT NOT NULL, s3_key TEXT NOT NULL, "
                "source_name TEXT NOT NULL, chunk_index INTEGER NOT NULL, "
                "content TEXT NOT NULL, embedding TEXT, metadata TEXT DEFAULT '{}', "
                "created_at TEXT)"
            )

    def test_purge_deletes_only_expired(self):
        import uuid
        from datetime import timedelta

        from django.test import override_settings
        from django.utils import timezone

        from apps.training_data.tasks import purge_old_rag_chunks

        self._ensure_table()
        from django.db import connection
        old = timezone.now() - timedelta(days=400)
        new = timezone.now() - timedelta(days=10)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO rag_knowledge_chunks (id, doc_id, s3_key, source_name,"
                " chunk_index, content, created_at) VALUES (%s, %s, %s, %s, 0, %s, %s)",
                [str(uuid.uuid4()), str(uuid.uuid4()), "d/old.pdf", "old", "viejo", old],
            )
            cursor.execute(
                "INSERT INTO rag_knowledge_chunks (id, doc_id, s3_key, source_name,"
                " chunk_index, content, created_at) VALUES (%s, %s, %s, %s, 0, %s, %s)",
                [str(uuid.uuid4()), str(uuid.uuid4()), "d/new.pdf", "new", "nuevo", new],
            )
        with override_settings(CHUNK_RETENTION_DAYS=365):
            out = purge_old_rag_chunks.run()
        self.assertEqual(out["deleted"], 1)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM rag_knowledge_chunks")
            self.assertEqual(cursor.fetchone()[0], 1)
