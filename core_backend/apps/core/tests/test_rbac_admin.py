"""RBAC administrativo V2 (web retirada; admin = Django nativo).

- Grupo Botánico: idempotente, exactamente 6 view-perms.
- Botánico (staff+grupo): ve changelists, no puede add (403).
- Staff sin grupo: 403 en módulos de auditoría.
- SuperAdmin: acceso total.
- /privacy/ pública (Data Safety APK).
"""
import sys

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, RequestFactory, override_settings

from apps.ai_models.models import LLMRequest
from apps.core.models import AIDiagnostic
from apps.core.services.rbac import (
    BOTANICO_GROUP,
    botanico_can_audit,
    ensure_botanico_group,
)

User = get_user_model()

needs_django_templates = pytest.mark.skipif(
    sys.version_info >= (3, 14),
    reason="Django 4.2 no renderiza templates en Python 3.14 "
           "(verificado OK en 3.12 de CI/compose); se valida por permisos.",
)


@pytest.fixture(autouse=True)
def _locmem_cache():
    # Sin Redis local, auth/throttles degradan (issue 10); locmem aísla.
    with override_settings(CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }):
        yield

User = get_user_model()

WANT = {
    "view_aidiagnostic",
    "view_ambientreading",
    "view_device",
    "view_llmrequest",
    "view_sensorlog",
    "view_soilreading",
}


@pytest.mark.django_db
def test_ensure_botanico_group_idempotente_y_exacta():
    g1, _ = ensure_botanico_group()
    g2, changed = ensure_botanico_group()
    assert g1.pk == g2.pk
    assert changed is False
    assert {p.codename for p in g1.permissions.all()} == WANT
    assert Group.objects.filter(name=BOTANICO_GROUP).count() == 1


@pytest.mark.django_db
def test_botanico_ve_pero_no_agrega():
    staff = User.objects.create_user(username="bot1", password="x", is_staff=True)
    staff.groups.add(Group.objects.get(name=BOTANICO_GROUP))
    assert botanico_can_audit(staff) is True
    # Permisos a nivel objeto (sin render: corre en cualquier Python).
    rf = RequestFactory()
    req = rf.get("/admin/core/aidiagnostic/")
    req.user = staff
    ma = admin.site._registry[AIDiagnostic]
    assert ma.has_view_permission(req) is True
    assert ma.has_add_permission(req) is False
    assert ma.has_delete_permission(req) is False
    ml = admin.site._registry[LLMRequest]
    assert ml.has_view_permission(req) is True
    assert ml.has_add_permission(req) is False
    # NOTA: el render GET real vive en test_botanico_changelist_render
    # (skip en Python 3.14 por incompatibilidad de templates Django 4.2).


@needs_django_templates
@pytest.mark.django_db
def test_botanico_changelist_render():
    staff = User.objects.create_user(username="bot2", password="x", is_staff=True)
    staff.groups.add(Group.objects.get(name=BOTANICO_GROUP))
    c = Client()
    c.force_login(staff)
    assert c.get("/admin/core/aidiagnostic/").status_code == 200
    assert c.get("/admin/ai_models/llmrequest/").status_code == 200
    # Sin add-perm → 403 en el formulario de alta.
    assert c.get("/admin/core/aidiagnostic/add/").status_code == 403


@pytest.mark.django_db
def test_staff_sin_grupo_403():
    staff = User.objects.create_user(username="plain", password="x", is_staff=True)
    assert botanico_can_audit(staff) is False
    c = Client()
    c.force_login(staff)
    assert c.get("/admin/core/aidiagnostic/").status_code == 403


@needs_django_templates
@pytest.mark.django_db
def test_superadmin_total():
    admin = User.objects.create_superuser(
        username="root", password="x", email="r@r.mx")
    assert botanico_can_audit(admin) is True
    c = Client()
    c.force_login(admin)
    assert c.get("/admin/core/aidiagnostic/").status_code == 200
    assert c.get("/admin/core/auditlog/").status_code == 200


@pytest.mark.django_db
def test_privacy_publica():
    resp = Client().get("/privacy/")
    assert resp.status_code == 200
    assert b"LFPDPPP" in resp.content
