"""Consentimiento LFPDPPP (Art. 8, BR-02) — única implementación.

Tanto `consent_view` (otorgar/revocar post-registro) como `register_view`
(consentimiento al alta) persisten vía :func:`record_consent`: flag
`data_consent`, fecha (`NULL` al revocar) y `AuditLog` inmutable.
"""
from django.utils import timezone

from apps.core.models import AuditLog


def record_consent(user, granted, ip_address=None):
    """Persiste el consentimiento y lo audita. Retorna `(data_consent, date)`."""
    user.data_consent = bool(granted)
    user.data_consent_date = timezone.now() if granted else None
    user.save(update_fields=["data_consent", "data_consent_date", "updated_at"])
    AuditLog.objects.create(
        user_id=user.id,
        action="CONSENT_GRANTED" if granted else "CONSENT_REVOKED",
        ip_address=ip_address,
        details=f"LFPDPPP consent set to {bool(granted)}.",
    )
    return user.data_consent, user.data_consent_date


def record_ai_consent(user, granted, ip_address=None):
    """Consentimiento IA separado (S3): diagnóstico por foto y chat RAG.
    Sin otorgar, los endpoints IA responden 403 CONSENT_REQUIRED."""
    user.ai_consent = bool(granted)
    user.ai_consent_date = timezone.now() if granted else None
    user.save(update_fields=["ai_consent", "ai_consent_date", "updated_at"])
    AuditLog.objects.create(
        user_id=user.id,
        action="AI_CONSENT_GRANTED" if granted else "AI_CONSENT_REVOKED",
        ip_address=ip_address,
        details=f"AI consent set to {bool(granted)}.",
    )
    return user.ai_consent, user.ai_consent_date


def require_ai_consent(user):
    """True si el usuario puede usar inferencia IA."""
    return bool(getattr(user, "ai_consent", False))
