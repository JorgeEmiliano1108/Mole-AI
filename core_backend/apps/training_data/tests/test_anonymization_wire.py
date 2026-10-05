"""Tests de wire del pipeline de anonimización (issues trace/28 + anonim/02-04)."""
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone

from apps.authentication.erasure import purge_user_data
from apps.core.models import AIDiagnostic
from apps.training_data.anonymization import (
    AnonymizationService,
    export_user_dataset,
)
from apps.training_data.models import (
    ProcessingStatus,
    TrainingDatasetAnon,
    TrainingDocument,
    TrainingImage,
)
from apps.training_data.tasks import export_anonymized_dataset

User = get_user_model()


@pytest.fixture
def anon_user(db):
    return User.objects.create_user(username="anonu", password="pw")


@override_settings(ANONIMIZACION_KEY="wire-anon-key")
def test_export_user_dataset_creates_anon_records(anon_user):
    plant_id = uuid4()
    AIDiagnostic.objects.create(
        user=anon_user,
        plant_id=plant_id,
        diagnosis_label="roya",
        confidence_score=0.91,
        metadata={"severity": "low"},
        analyzed_at=timezone.now(),
    )
    TrainingDocument.objects.create(
        uploaded_by=anon_user,
        s3_key="docs/uuid.pdf",
        s3_bucket="mole-training-data",
        original_name="diagnostico.pdf",
        content_type="application/pdf",
        file_size=1024,
        category="enfermedad",
        status=ProcessingStatus.INDEXED,
    )
    TrainingImage.objects.create(
        uploaded_by=anon_user,
        s3_key="images/uuid.jpg",
        s3_bucket="mole-training-data",
        original_name="hoja.jpg",
        content_type="image/jpeg",
        file_size=2048,
        disease_label="roya",
        status=ProcessingStatus.INDEXED,
    )

    created, _ = export_user_dataset(anon_user)
    assert created == 3

    anon = TrainingDatasetAnon.objects.all()
    assert anon.filter(record_type="diagnostic").count() == 1
    assert anon.filter(record_type="document").count() == 1
    assert anon.filter(record_type="image").count() == 1

    # Sin PII en payload ni en columnas
    for rec in anon:
        payload = rec.feature_payload
        assert "original_name" not in payload
        assert "image_path" not in payload
        assert "user_id" not in payload
        assert "email" not in payload
        # subject_hash es HMAC, no el UUID crudo.
        assert len(rec.subject_hash) == 64


@override_settings(ANONIMIZACION_KEY="wire-anon-key")
def test_export_user_dataset_is_idempotent_and_marks_purged(anon_user):
    AIDiagnostic.objects.create(
        user=anon_user,
        plant_id=uuid4(),
        diagnosis_label="roya",
        confidence_score=0.8,
        analyzed_at=timezone.now(),
    )
    export_user_dataset(anon_user, purged=False)
    assert TrainingDatasetAnon.objects.count() == 1
    assert TrainingDatasetAnon.objects.filter(purged=True).count() == 0

    # Segunda exportación con purged=True actualiza el flag sin duplicar.
    export_user_dataset(anon_user, purged=True)
    assert TrainingDatasetAnon.objects.count() == 1
    assert TrainingDatasetAnon.objects.filter(purged=True).count() == 1


@override_settings(ANONIMIZACION_KEY="wire-anon-key")
def test_purge_user_data_exports_before_delete(anon_user):
    AIDiagnostic.objects.create(
        user=anon_user,
        plant_id=uuid4(),
        diagnosis_label="mildiu",
        confidence_score=0.85,
        analyzed_at=timezone.now(),
    )
    TrainingDocument.objects.create(
        uploaded_by=anon_user,
        s3_key="docs/x.pdf",
        s3_bucket="mole-training-data",
        original_name="x.pdf",
        content_type="application/pdf",
        file_size=1,
        status=ProcessingStatus.INDEXED,
    )

    counts = purge_user_data(anon_user)
    assert counts["training_anon_records"] == 2
    assert TrainingDatasetAnon.objects.filter(purged=True).count() == 2
    assert AIDiagnostic.objects.filter(user=anon_user).count() == 0
    assert TrainingDocument.objects.filter(uploaded_by=anon_user).count() == 0


@override_settings(ANONIMIZACION_KEY="wire-anon-key")
def test_export_anonymized_dataset_task(anon_user):
    AIDiagnostic.objects.create(
        user=anon_user,
        plant_id=uuid4(),
        diagnosis_label="roya",
        confidence_score=0.9,
        analyzed_at=timezone.now(),
    )
    result = export_anonymized_dataset.run(str(anon_user.id), purged=False)
    assert result["created"] == 1
    assert result["purged"] is False
    assert TrainingDatasetAnon.objects.count() == 1


@override_settings(ANONIMIZACION_KEY="wire-anon-key")
def test_anonymization_service_methods(anon_user):
    doc = TrainingDocument.objects.create(
        uploaded_by=anon_user,
        s3_key="docs/y.pdf",
        s3_bucket="mole-training-data",
        original_name="y.pdf",
        content_type="application/pdf",
        file_size=1,
        category="plaga",
        status=ProcessingStatus.INDEXED,
    )
    svc = AnonymizationService()
    rec = svc.anonymize_document(doc)
    assert rec.record_type == "document"
    assert rec.label == "plaga"
    assert rec.feature_payload["category"] == "plaga"
    assert "original_name" not in rec.feature_payload
