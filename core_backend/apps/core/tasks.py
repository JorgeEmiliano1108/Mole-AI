from celery import shared_task
import uuid
import os
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.plants.models import UserPlant

@shared_task(name="generate_master_report_task")
def generate_master_report_task():
    """
    Generates a master JSON report asynchronously.
    """
    User = get_user_model()
    report_filename = f"report_master_{uuid.uuid4().hex[:8]}.json"
    
    media_dir = os.path.join(settings.BASE_DIR, 'media', 'reports')
    os.makedirs(media_dir, exist_ok=True)
    file_path = os.path.join(media_dir, report_filename)
    
    from apps.core.models import SensorLog
    from django.db.models import Avg

    aggs = SensorLog.objects.aggregate(
        avg_hum=Avg('soil_humidity'),
        avg_ph=Avg('ph_level')
    )
    
    data = {
        "report_id": report_filename,
        "total_users": User.objects.count(),
        "total_plants": UserPlant.objects.count(),
        "avg_humidity": aggs['avg_hum'] or 0,
        "avg_ph": aggs['avg_ph'] or 0,
        "status": "COMPLETED"
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
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            # Using CONCURRENTLY avoids locking the view while it refreshes.
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY admin_stats;")
        return "Materialized view refreshed successfully"
    return "Skipped refresh (not using postgresql)"
