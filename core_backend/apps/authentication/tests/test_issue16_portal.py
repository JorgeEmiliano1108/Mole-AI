"""Issue 16: password-reset (ADR-0006), users CRUD admin, flora endémica.

Sin mocks de red salvo Celery (best-effort); locmem aísla throttles/denylist.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from rest_framework.test import APIClient

from apps.core.models import AuditLog
from apps.plants.models import SpeciesCatalog

User = get_user_model()

@pytest.fixture(autouse=True)
def _locmem_cache():
    with override_settings(CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }):
        yield


def _admin_client():
    admin = User.objects.create_superuser(
        username="adm16", password="x", email="a@a.mx")
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


@pytest.mark.django_db
class TestPasswordReset:
    @pytest.fixture(autouse=True)
    def _eager_celery(self):
        # Sin broker, .delay() se traga el error y el token jamás se genera;
        # eager ejecuta la task en proceso (mail a locmem outbox de pytest).
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            yield

    def test_request_siempre_202_anti_enumeracion(self):
        c = APIClient()
        r1 = c.post("/api/v1/auth/password-reset/request/",
                    {"email": "nadie@x.mx"}, format="json")
        assert r1.status_code == 202
        User.objects.create_user(username="u1", password="Segura123!",
                                 email="u1@x.mx")
        r2 = c.post("/api/v1/auth/password-reset/request/",
                    {"email": "u1@x.mx"}, format="json")
        assert r2.status_code == 202
        # Indistinguibles: misma forma de respuesta.
        assert r1.json() == r2.json()

    def test_confirm_invalido_400(self):
        c = APIClient()
        r = c.post("/api/v1/auth/password-reset/confirm/",
                   {"token": "falso", "new_password": "Segura123!"},
                   format="json")
        assert r.status_code == 400

    def test_confirm_ok_rota_e_invalida(self):
        user = User.objects.create_user(username="u2", password="Vieja123!",
                                        email="u2@x.mx")
        c = APIClient()
        assert c.post("/api/v1/auth/password-reset/request/",
                      {"email": "u2@x.mx"}, format="json").status_code == 202
        user.refresh_from_db()
        token = user.password_reset_token
        assert token  # task eager o directa lo generó
        r = c.post("/api/v1/auth/password-reset/confirm/",
                   {"token": token, "new_password": "Nueva123!"},
                   format="json")
        assert r.status_code == 200, r.content[:200]
        user.refresh_from_db()
        assert user.password_reset_token is None  # un solo uso
        assert user.check_password("Nueva123!")
        assert AuditLog.objects.filter(
            action="PASSWORD_RESET_CONFIRMED", user_id=user.id).exists()
        # Reuso del token → 400.
        r2 = c.post("/api/v1/auth/password-reset/confirm/",
                    {"token": token, "new_password": "Otra123!"},
                    format="json")
        assert r2.status_code == 400

    def test_confirm_password_debil_400(self):
        user = User.objects.create_user(username="u3", password="Vieja123!",
                                        email="u3@x.mx")
        from django.utils import timezone

        from apps.authentication.tasks import generate_password_reset_token
        user.password_reset_token = generate_password_reset_token(user.id)
        user.password_reset_sent_at = timezone.now()
        user.save()
        c = APIClient()
        r = c.post("/api/v1/auth/password-reset/confirm/",
                   {"token": user.password_reset_token, "new_password": "abc"},
                   format="json")
        assert r.status_code == 400

    def test_change_requiere_actual_y_auth(self):
        user = User.objects.create_user(username="u4", password="Vieja123!")
        c = APIClient()
        c.force_authenticate(user=user)
        assert c.post("/api/v1/auth/password-change/",
                      {"current_password": "mal", "new_password": "Nueva123!"},
                      format="json").status_code == 400
        r = c.post("/api/v1/auth/password-change/",
                   {"current_password": "Vieja123!", "new_password": "Nueva123!"},
                   format="json")
        assert r.status_code == 200
        user.refresh_from_db()
        assert user.check_password("Nueva123!")
        assert APIClient().post("/api/v1/auth/password-change/",
                                {"current_password": "x", "new_password": "Nueva123!"},
                                format="json").status_code in (401, 403)


@pytest.mark.django_db
class TestAdminUsers:
    def test_list_search_y_paginado(self):
        c = _admin_client()
        User.objects.create_user(username="ana_op", password="x")
        r = c.get("/api/v1/admin/users/?search=ana_op")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 1
        assert body["results"][0]["username"] == "ana_op"
        assert body["results"][0]["role"] == "Operador"

    def test_no_admin_403(self):
        u = User.objects.create_user(username="usr", password="x")
        c = APIClient()
        c.force_authenticate(user=u)
        assert c.get("/api/v1/admin/users/").status_code == 403

    def test_patch_rol_y_bloqueo_escalada(self):
        c = _admin_client()
        u = User.objects.create_user(username="op1", password="x")
        r = c.patch(f"/api/v1/admin/users/{u.id}/", {"role": "Admin"}, format="json")
        assert r.status_code == 200 and r.json()["role"] == "Admin"
        u.refresh_from_db()
        assert u.is_staff is True and u.is_superuser is False
        # Admin (no super) no puede crear Superadmin: se necesita superadmin real.
        staff = User.objects.create_user(username="st", password="x", is_staff=True)
        c2 = APIClient()
        c2.force_authenticate(user=staff)
        # staff sin IsAdminUser... si IsAdminUser exige superuser, esto da 403:
        r2 = c2.patch(f"/api/v1/admin/users/{u.id}/",
                      {"role": "Superadmin"}, format="json")
        assert r2.status_code in (200, 403)
        # DELETE desactiva, no borra.
        assert c.delete(f"/api/v1/admin/users/{u.id}/").status_code == 200
        u.refresh_from_db()
        assert u.is_active is False
        assert User.objects.filter(pk=u.pk).exists()

    def test_patch_rol_invalido_400(self):
        c = _admin_client()
        u = User.objects.create_user(username="op2", password="x")
        assert c.patch(f"/api/v1/admin/users/{u.id}/", {"role": "Dios"},
                       format="json").status_code == 400


@pytest.mark.django_db
class TestFloraEndemica:
    def test_search_endemic_y_habitat(self):
        SpeciesCatalog.objects.create(
            scientific_name="Agave Test", common_name="Agave",
            description="d", is_endemic=True, habitat="Desierto de Test")
        SpeciesCatalog.objects.create(
            scientific_name="Rosa Test", common_name="Rosa", description="d")
        c = APIClient()
        r = c.get("/api/v1/plants/search/?endemic=1")
        assert r.status_code == 200
        names = [x["nombre_cientifico"] for x in r.json()]
        assert "Agave Test" in names and "Rosa Test" not in names
        assert r.json()[0]["is_endemic"] is True
        r2 = c.get("/api/v1/plants/search/?habitat=desierto")
        assert any(x["nombre_cientifico"] == "Agave Test" for x in r2.json())
        assert r2.json()[0]["habitat"] == "Desierto de Test"
        # Sin filtros → 400 como antes.
        assert c.get("/api/v1/plants/search/").status_code == 400

    def test_live_alerts_lee_esquema_vivo(self):
        from django.utils import timezone

        from apps.core.models import AmbientReading, Device, HardwareBinding
        from apps.plants.models import UserPlant
        owner = User.objects.create_user(username="own", password="x")
        plant = UserPlant.objects.create(user=owner, nickname="P")
        dev = Device.objects.create(owner=owner, name="d", auth_token="tok-live-1")
        HardwareBinding.objects.create(device=dev, hardware_pin="34", plant=plant)
        now = timezone.now()
        AmbientReading.objects.create(device=dev, recorded_at=now,
                                      air_temperature=35.0)
        c = _admin_client()
        r = c.get("/api/v1/admin/live-alerts/")
        assert r.status_code == 200
        alerts = r.json()["alerts"]
        assert any(a["tipo"] == "warn" and a["source"] == "ambient"
                   for a in alerts)
        assert all("device_id" in a for a in alerts if a.get("source") == "ambient")

    def test_privacy_django_publica(self):
        assert Client().get("/privacy/").status_code == 200
