"""Consentimiento LFPDPPP en backend (BR-02).

- POST /auth/consent/ {consent:true} → 200, persiste flag + fecha, audita.
- {consent:false} → revoca (fecha NULL), audita.
- Body inválido → 400. Sin auth → 401.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.core.models import AuditLog

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="consent1", email="c1@mole.ai", password="x")


@pytest.mark.django_db
def test_consent_otorgar_persiste_y_audita(user):
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post("/api/v1/auth/consent/", {"consent": True}, format="json")
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.data_consent is True
    assert user.data_consent_date is not None
    assert AuditLog.objects.filter(action="CONSENT_GRANTED").exists()


@pytest.mark.django_db
def test_consent_revocar_limpia_fecha(user):
    client = APIClient()
    client.force_authenticate(user=user)
    client.post("/api/v1/auth/consent/", {"consent": True}, format="json")
    resp = client.post("/api/v1/auth/consent/", {"consent": False}, format="json")
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.data_consent is False
    assert user.data_consent_date is None
    assert AuditLog.objects.filter(action="CONSENT_REVOKED").exists()


@pytest.mark.django_db
def test_consent_body_invalido_400(user):
    client = APIClient()
    client.force_authenticate(user=user)
    assert client.post("/api/v1/auth/consent/", {"consent": "si"}, format="json").status_code == 400
    assert client.post("/api/v1/auth/consent/", {}, format="json").status_code == 400


@pytest.mark.django_db
def test_consent_sin_auth_401(db):
    assert APIClient().post("/api/v1/auth/consent/", {"consent": True}, format="json").status_code == 401


@pytest.mark.django_db
def test_register_sin_consent_400():
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/register/",
        {"username": "nuevo1", "password": "Segura123!"},
        format="json",
    )
    assert resp.status_code == 400
    assert "LFPDPPP" in resp.json().get("error", "")
    assert not User.objects.filter(username="nuevo1").exists()


@pytest.mark.django_db
def test_register_con_consent_persiste_y_audita():
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/register/",
        {"username": "nuevo2", "password": "Segura123!", "consent": True},
        format="json",
    )
    assert resp.status_code == 201, resp.content[:200]
    user = User.objects.get(username="nuevo2")
    assert user.data_consent is True
    assert user.data_consent_date is not None
    assert AuditLog.objects.filter(
        action="CONSENT_GRANTED", user_id=user.id
    ).exists()
