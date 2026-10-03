"""Tests de Track B: tabla espejo training_dataset_anon + Repository + HMAC."""
import hashlib
import hmac
from types import SimpleNamespace
from uuid import uuid4

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.training_data.anonymization import AnonymizationService
from apps.training_data.models import TrainingDatasetAnon
from apps.training_data.repositories import DjangoAnonymizationRepository


@override_settings(ANONIMIZACION_KEY="test-anon-key")
class AnonymizationSchemaTests(TestCase):
    def test_schema_has_no_pii_fields(self):
        field_names = {f.name for f in TrainingDatasetAnon._meta.get_fields()}
        assert "user" not in field_names
        assert "image_path" not in field_names
        assert "subject_hash" in field_names
        assert "feature_payload" in field_names
        assert TrainingDatasetAnon._meta.db_table == "training_dataset_anon"


@override_settings(ANONIMIZACION_KEY="test-anon-key")
class AnonymizationServiceTests(TestCase):
    def _diagnostic(self, user_id=7, plant_id=None, label="roya"):
        return SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            plant_id=plant_id or uuid4(),
            diagnosis_label=label,
            confidence_score=0.91,
            pvu_reason="PVU-OK",
            metadata={"severity": "low"},
            analyzed_at=timezone.now(),
        )

    def test_hmac_is_deterministic(self):
        svc = AnonymizationService()
        self.assertEqual(svc.hmac_hex("a", "b"), svc.hmac_hex("a", "b"))
        self.assertNotEqual(svc.hmac_hex("a", "b"), svc.hmac_hex("a", "c"))

    def test_hmac_matches_reference_implementation(self):
        svc = AnonymizationService()
        expected = hmac.new(b"test-anon-key", b"x|y", hashlib.sha256).hexdigest()
        self.assertEqual(svc.hmac_hex("x", "y"), expected)

    def test_anonymize_omits_pii_and_groups_subject(self):
        plant = uuid4()
        svc = AnonymizationService()
        rec1 = svc.anonymize_diagnostic(self._diagnostic(user_id=7, plant_id=plant))
        rec2 = svc.anonymize_diagnostic(self._diagnostic(user_id=7, plant_id=plant))

        # Agrupación determinista por sujeto, fuentes distintas.
        self.assertEqual(rec1.subject_hash, rec2.subject_hash)
        self.assertNotEqual(rec1.source_fingerprint, rec2.source_fingerprint)
        # Sin PII en el payload ni en columnas.
        self.assertNotIn("image_path", rec1.feature_payload)
        self.assertNotIn("user", rec1.feature_payload)
        self.assertEqual(rec1.feature_payload["diagnosis_label"], "roya")
        self.assertEqual(rec1.label, "roya")

    def test_missing_key_raises(self):
        with override_settings(ANONIMIZACION_KEY=""):
            with self.assertRaises(ImproperlyConfigured):
                AnonymizationService()


@override_settings(ANONIMIZACION_KEY="test-anon-key")
class AnonymizationRepositoryTests(TestCase):
    def test_save_and_find_by_subject_hash(self):
        repo = DjangoAnonymizationRepository()
        rec = repo.save(TrainingDatasetAnon(
            record_type="diagnostic",
            source_fingerprint="fp-1",
            subject_hash="subject-abc",
            feature_payload={"diagnosis_label": "roya"},
            label="roya",
        ))
        assert rec.pk is not None
        results = list(repo.find_by_subject_hash("subject-abc"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].feature_payload["diagnosis_label"], "roya")
        self.assertEqual(list(repo.find_by_subject_hash("subject-otro")), [])
