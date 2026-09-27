import uuid

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import AIDiagnostic
from apps.core.services.safety_validator import SafetyValidator

User = get_user_model()


@pytest.fixture
def safety_validator():
    return SafetyValidator()


@pytest.fixture
def authenticated_client(db):
    user = User.objects.create_user(username="safetyuser", password="pw")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def diagnostic(db, authenticated_client):
    _, user = authenticated_client
    return AIDiagnostic.objects.create(
        user=user,
        plant_id=uuid.uuid4(),
        diagnosis_label="Mildiu",
    )


# -----------------------------------------------------------------------------
# Unitarios directos al SafetyValidator
# -----------------------------------------------------------------------------
class TestSafetyValidatorUnit:
    def test_safe_text_returns_ok(self, safety_validator):
        result = safety_validator.validate({"text": "Todo normal en el cultivo"})
        assert result.safe is True
        assert result.code == "SAFETY_OK"

    def test_nom059_species_in_text_blocked(self, safety_validator):
        result = safety_validator.validate({"text": "Encontré un peyote en el terreno"})
        assert result.safe is False
        assert result.code == "SAFETY_NOM059_PROTECTED"
        assert "NOM-059" in result.reason

    def test_nom059_scientific_name_blocked(self, safety_validator):
        result = safety_validator.validate({"text": "Lophophora williamsii detectada"})
        assert result.safe is False
        assert result.code == "SAFETY_NOM059_PROTECTED"

    def test_agrochemical_dose_exceeded_blocked(self, safety_validator):
        result = safety_validator.validate({
            "agrochemical_id": "sulfato_de_cobre",
            "dose_per_hectare": 3000,
        })
        assert result.safe is False
        assert result.code == "SAFETY_DOSE_EXCEEDED"
        assert "3000" in result.reason

    def test_agrochemical_applications_exceeded_blocked(self, safety_validator):
        result = safety_validator.validate({
            "agrochemical_id": "glifosato_isopropilamina",
            "applications": 5,
        })
        assert result.safe is False
        assert result.code == "SAFETY_APPLICATIONS_EXCEEDED"

    def test_restricted_crop_blocked(self, safety_validator):
        result = safety_validator.validate({
            "agrochemical_id": "sulfato_de_cobre",
            "crop": "tomate en invernadero orgánico",
        })
        assert result.safe is False
        assert result.code == "SAFETY_RESTRICTED_CROP"

    def test_forbidden_region_blocked(self, safety_validator):
        result = safety_validator.validate({
            "agrochemical_id": "glifosato_isopropilamina",
            "region": "área natural protegida federal",
        })
        assert result.safe is False
        assert result.code == "SAFETY_FORBIDDEN_REGION"

    def test_unauthorized_combination_blocked(self, safety_validator):
        result = safety_validator.validate({
            "agrochemical_id": "sulfato_de_cobre",
            "combination_ids": ["caldo_borholes"],
        })
        assert result.safe is False
        assert result.code == "SAFETY_UNAUTHORIZED_COMBINATION"

    def test_unknown_agrochemical_blocked_by_fallback(self, safety_validator):
        result = safety_validator.validate({"agrochemical_id": "agente_desconocido_x"})
        assert result.safe is False
        assert result.code == "SAFETY_DATA_MISSING"

    def test_safe_agrochemical_within_limits(self, safety_validator):
        result = safety_validator.validate({
            "agrochemical_id": "sulfato_de_cobre",
            "dose_per_hectare": 2000,
            "applications": 2,
            "crop": "maíz",
            "region": "campo comercial",
        })
        assert result.safe is True


# -----------------------------------------------------------------------------
# Red-Team vía API REST
# -----------------------------------------------------------------------------
@pytest.mark.django_db
class TestSafetyRedTeamAPI:
    def test_valid_payload_returns_safe(self, authenticated_client):
        client, _ = authenticated_client
        response = client.post(
            reverse("core:safety_validate"),
            {"text": "Cultivo sano", "agrochemical_id": "sulfato_de_cobre", "dose_per_hectare": 1000},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["safe"] is True

    def test_injected_nom059_species_blocked_with_403(self, authenticated_client):
        client, _ = authenticated_client
        response = client.post(
            reverse("core:safety_validate"),
            {"text": "Voy a transplantar Mammillaria herrerae"},
            format="json",
        )
        assert response.status_code == 403
        body = response.json()
        assert body["safe"] is False
        assert body["code"] == "SAFETY_NOM059_PROTECTED"
        assert "NOM-059" in body["reason"]

    def test_injected_overdose_blocked_with_403(self, authenticated_client):
        client, _ = authenticated_client
        response = client.post(
            reverse("core:safety_validate"),
            {
                "agrochemical_id": "glifosato_isopropilamina",
                "dose_per_hectare": 10.0,
            },
            format="json",
        )
        assert response.status_code == 403
        body = response.json()
        assert body["safe"] is False
        assert body["code"] == "SAFETY_DOSE_EXCEEDED"


# -----------------------------------------------------------------------------
# Integración: PATCH /api/v1/diagnostics/<id>/ intercepta pvu_reason
# -----------------------------------------------------------------------------
@pytest.mark.django_db
class TestSafetyDiagnosticPatchIntegration:
    def test_safe_pvu_reason_updates(self, authenticated_client, diagnostic):
        client, _ = authenticated_client
        url = reverse("core:diagnostic_patch", kwargs={"id": diagnostic.id})
        response = client.patch(url, {"pvu_reason": "conexión estable"}, format="json")
        assert response.status_code == 200
        diagnostic.refresh_from_db()
        assert diagnostic.pvu_reason == "conexión estable"

    def test_nom059_pvu_reason_blocked_before_save(self, authenticated_client, diagnostic):
        client, _ = authenticated_client
        url = reverse("core:diagnostic_patch", kwargs={"id": diagnostic.id})
        response = client.patch(url, {"pvu_reason": "peyote encontrado"}, format="json")
        assert response.status_code == 403
        diagnostic.refresh_from_db()
        assert diagnostic.pvu_reason != "peyote encontrado"
        assert diagnostic.pvu_reason is None

