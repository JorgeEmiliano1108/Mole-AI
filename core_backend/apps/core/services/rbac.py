"""RBAC administrativo V2 (web retirada; admin = Django nativo).

- SuperAdmin: `is_superuser` nativo, acceso total (sin grupo).
- Botánico: `is_staff` + grupo con permisos SOLO-VIEW sobre diagnósticos,
  telemetría IoT y logs RAG. `ensure_botanico_group()` es idempotente y la
  usan tanto la migración 0014 como los tests.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.ai_models.models import LLMRequest
from apps.core.models import (
    AIDiagnostic,
    AmbientReading,
    Device,
    SensorLog,
    SoilReading,
)

BOTANICO_GROUP = "Botánico"

# (app_label, model) con acceso de auditoría solo-lectura.
BOTANICO_MODELS = [
    ("core", "aidiagnostic"),
    ("core", "device"),
    ("core", "ambientreading"),
    ("core", "soilreading"),
    ("core", "sensorlog"),
    ("ai_models", "llmrequest"),
]

_MODEL_CLASSES = {
    ("core", "aidiagnostic"): AIDiagnostic,
    ("core", "device"): Device,
    ("core", "ambientreading"): AmbientReading,
    ("core", "soilreading"): SoilReading,
    ("core", "sensorlog"): SensorLog,
    ("ai_models", "llmrequest"): LLMRequest,
}


def ensure_botanico_group():
    """Crea/actualiza el grupo Botánico con exactamente los view-perms.

    Idempotente y seguro de re-ejecutar: usa get_or_create en Grupo,
    ContentType y Permission (las Permission de auth se crean post-migrate,
    por eso no se asume su existencia).
    Retorna (group, created).
    """
    group, _ = Group.objects.get_or_create(name=BOTANICO_GROUP)
    wanted = set()
    for app_label, model_name in BOTANICO_MODELS:
        ct = ContentType.objects.get_for_model(
            _MODEL_CLASSES[(app_label, model_name)]
        )
        perm, _ = Permission.objects.get_or_create(
            codename=f"view_{model_name}",
            content_type=ct,
            defaults={"name": f"Can view {model_name}"},
        )
        wanted.add(perm.pk)
    current = set(group.permissions.values_list("pk", flat=True))
    if current != wanted:
        group.permissions.set(Permission.objects.filter(pk__in=wanted))
    return group, current != wanted


def botanico_can_audit(user):
    """True si el usuario puede auditar (staff+grupo o superuser)."""
    if user.is_superuser:
        return True
    return (
        user.is_staff
        and user.groups.filter(name=BOTANICO_GROUP).exists()
    )
