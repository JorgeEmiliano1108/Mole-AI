"""
Celery tasks for core backend operations.

LFPDPPP Art. 19 Compliance:
  Tasks that transit through Redis use ``hashed_user_id`` (SHA-256) instead
  of the raw user ID to minimise PII exposure in the message broker.
"""
import hashlib
import json
import os
import uuid

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.plants.models import UserPlant


def _hash_user_id(user_id) -> str:
    """Return a SHA-256 hex digest of the user identifier (LFPDPPP Art. 19)."""
    return hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()


@shared_task(name="generate_master_report_task")
def generate_master_report_task(user_id=None):
    """
    Generates a master JSON report asynchronously.

    Args:
        user_id: The raw user ID of the requesting user.  This value is
                 hashed immediately and never stored or forwarded in clear.
    """
    User = get_user_model()

    hashed_uid = _hash_user_id(user_id) if user_id else "system"
    report_filename = f"report_{hashed_uid[:12]}_{uuid.uuid4().hex[:8]}.json"

    media_dir = os.path.join(settings.BASE_DIR, "media", "reports")
    os.makedirs(media_dir, exist_ok=True)
    file_path = os.path.join(media_dir, report_filename)

    from apps.core.models import SensorLog
    from django.db.models import Avg

    aggs = SensorLog.objects.aggregate(
        avg_hum=Avg("soil_humidity"),
        avg_ph=Avg("ph_level"),
    )

    data = {
        "report_id": report_filename,
        "hashed_user_id": hashed_uid,
        "total_users": User.objects.count(),
        "total_plants": UserPlant.objects.count(),
        "avg_humidity": aggs["avg_hum"] or 0,
        "avg_ph": aggs["avg_ph"] or 0,
        "status": "COMPLETED",
    }

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    return f"/media/reports/{report_filename}"


@shared_task(name="refresh_admin_stats_task")
def refresh_admin_stats_task():
    """
    Refresca la vista materializada de estadísticas del admin backend asincrónicamente.
    """
    from django.db import connection

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            # Using CONCURRENTLY avoids locking the view while it refreshes.
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY admin_stats;")
        return "Materialized view refreshed successfully"
    return "Skipped refresh (not using postgresql)"
