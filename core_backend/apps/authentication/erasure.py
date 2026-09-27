"""Borrado real y portabilidad GDPR (S3, issue normativa).

`purge_user_data` elimina en cascada los datos del usuario antes del
anonimizado+`user.delete()`. Se conserva `AuditLog` (deber legal de
trazabilidad, documentado). Todo best-effort por área con conteos.
"""
import logging

logger = logging.getLogger(__name__)


def profile_export_data(user):
    """Portabilidad GDPR: dump legible de los datos del usuario."""
    from apps.ai_models.models import LLMRequest
    from apps.core.models import AIDiagnostic, Device
    from apps.plants.models import FavoritePlant, UserPlant
    from apps.training_data.models import TrainingDocument, TrainingImage

    return {
        "profile": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": getattr(user, "phone_number", None),
            "data_consent": getattr(user, "data_consent", False),
            "data_consent_date": str(getattr(user, "data_consent_date", None)),
            "ai_consent": getattr(user, "ai_consent", False),
            "ai_consent_date": str(getattr(user, "ai_consent_date", None)),
            "date_joined": str(getattr(user, "date_joined", None)),
        },
        "plants": list(UserPlant.objects.filter(user=user).values(
            "id", "nickname", "created_at")),
        "favorites": list(FavoritePlant.objects.filter(user=user).values(
            "id", "plant_id")),
        "devices": list(Device.objects.filter(owner=user).values(
            "id", "name", "status", "last_seen")),
        "diagnostics": list(AIDiagnostic.objects.filter(user=user).values(
            "id", "plant_id", "diagnosis_label", "confidence_score",
            "analyzed_at")),
        "chat_history": list(LLMRequest.objects.filter(user=user).values(
            "id", "request_type", "status", "created_at")),
        "training_documents": list(
            TrainingDocument.objects.filter(uploaded_by=user).values(
                "id", "original_name", "category", "content_type")),
        "training_images": list(
            TrainingImage.objects.filter(uploaded_by=user).values(
                "id", "original_name", "content_type")),
    }


def purge_user_data(user):
    """Elimina en cascada + purga Redis/MinIO. Retorna conteos por área."""
    from apps.ai_models.models import LLMRequest
    from apps.core.models import AIDiagnostic, Device, SensorLog
    from apps.plants.models import FavoritePlant, UserPlant
    from apps.training_data.models import TrainingDocument, TrainingImage

    counts = {}
    user_id = user.id
    plant_ids = list(UserPlant.objects.filter(user=user)
                     .values_list("id", flat=True))

    counts["sensor_logs"] = SensorLog.objects.filter(
        plant_id__in=plant_ids).delete()[0]
    counts["ai_diagnostics"] = (
        AIDiagnostic.objects.filter(user=user).delete()[0]
        + AIDiagnostic.objects.filter(plant_id__in=plant_ids).delete()[0])
    counts["llm_requests"] = LLMRequest.objects.filter(user=user).delete()[0]

    s3_targets = [(d.s3_bucket, d.s3_key)
                  for d in TrainingDocument.objects.filter(uploaded_by=user)]
    s3_targets += [(d.s3_bucket, d.s3_key)
                   for d in TrainingImage.objects.filter(uploaded_by=user)]
    counts["training_documents"] = TrainingDocument.objects.filter(
        uploaded_by=user).delete()[0]
    counts["training_images"] = TrainingImage.objects.filter(
        uploaded_by=user).delete()[0]
    counts["s3_objects_deleted"] = _purge_s3_objects(s3_targets)

    counts["devices"] = Device.objects.filter(owner=user).delete()[0]
    counts["plants"] = UserPlant.objects.filter(user=user).delete()[0]
    counts["favorites"] = FavoritePlant.objects.filter(user=user).delete()[0]
    counts["redis_keys"] = _purge_redis_keys(user_id)
    return counts


def _purge_s3_objects(targets):
    """Best-effort: borra objetos MinIO/S3 del usuario."""
    if not targets:
        return 0
    try:
        import boto3
        from django.conf import settings
        s3 = boto3.client(
            's3',
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
        )
        deleted = 0
        for bucket, key in targets:
            try:
                s3.delete_object(Bucket=bucket, Key=key)
                deleted += 1
            except Exception as exc:
                logger.warning("erasure: no se pudo borrar s3://%s/%s: %s",
                               bucket, key, exc)
        return deleted
    except Exception as exc:
        logger.warning("erasure: S3 no disponible: %s", exc)
        return 0


def _purge_redis_keys(user_id):
    """Best-effort: purga claves de caché/throttle del usuario."""
    try:
        from django.core.cache import caches
        cache = caches['default']
        purged = 0
        if hasattr(cache, 'delete_pattern'):
            for pattern in (f"*{user_id}*",):
                try:
                    purged += cache.delete_pattern(pattern) or 0
                except Exception:
                    pass
            return purged
        # LocMem u otros: barrido directo por si el backend lo expone.
        inner = getattr(cache, '_cache', None)
        if isinstance(inner, dict):
            doomed = [k for k in list(inner)
                      if str(user_id) in str(k)]
            for k in doomed:
                try:
                    cache.delete(k)
                    purged += 1
                except Exception:
                    pass
        return purged
    except Exception as exc:
        logger.warning("erasure: Redis no disponible: %s", exc)
        return 0
